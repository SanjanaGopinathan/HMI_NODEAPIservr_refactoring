from datetime import datetime
from typing import Dict, Any, List
from urllib.parse import urlparse
from fastapi import HTTPException
from app.mapper.sensor import SensorModel, SensorDetails, AlertRule, AlertSubscriber
from app.config import settings
from app.mapper.resolver import resolve_policy_subscribers, resolve_profile_safety
import logging

logger = logging.getLogger(__name__)


class AssetToSensorMapper:
    """Maps HMI asset to DT_ConfigStorage sensor format"""
    
    @staticmethod
    def extract_ip_port_from_url(url: str) -> tuple:
        """Extract IP and port from RTSP/ONVIF URL"""
        if not url:
            return "192.168.1.1", 80
        
        parsed = urlparse(url)
        ip = parsed.hostname or "192.168.1.1"
        port = parsed.port or 80
        return ip, port
    
    @staticmethod
    def extract_credentials_from_url(url: str) -> tuple:
        """Extract username and password from URL"""
        if not url:
            return "admin", "admin"
        
        parsed = urlparse(url)
        username = parsed.username or "admin"
        password = parsed.password or "admin"
        return username, password
    
    @staticmethod
    async def map_asset_to_sensor(
        asset: Dict[str, Any],
        policy_data: Dict[str, Any],
        profile_data: Dict[str, Any],
        personnel_data: List[Dict[str, Any]],
        primary_subscriber_id: str = None
    ) -> SensorModel:
        """Transform HMI asset to DT_ConfigStorage sensor
        
        Args:
            asset: HMI asset document from hmi/assets collection
            policy_data: Complete policy document from hmi_db.policies
            profile_data: Complete profile document from hmi_db.profiles
            personnel_data: List of personnel documents for all PERSON targets
            primary_subscriber_id: Primary subscriber tel number for root subscriber_id field
            
        Returns:
            SensorModel ready for upsert to DT_ConfigStorage/sensors
            
        Raises:
            HTTPException(400): Missing required bindings or fields
            HTTPException(404): Policy/profile/personnel not found
        """
        asset_id = asset.get("_id", "UNKNOWN")
        
        # Extract bindings
        bindings = asset.get("asset_info", {}).get("bindings", {})
        policy_id = bindings.get("assigned_policy_id")
        profile_ids = bindings.get("target_profile_ids", [])
        profile_id = profile_ids[0] if profile_ids else None
        
        # Validate required bindings
        if not policy_id:
            logger.error(f"Asset missing assigned_policy_id: {asset_id}")
            raise HTTPException(
                status_code=400,
                detail=f"Asset '{asset_id}' missing required field: asset_info.bindings.assigned_policy_id"
            )
        
        if not profile_id:
            logger.error(f"Asset missing target_profile_ids: {asset_id}")
            raise HTTPException(
                status_code=400,
                detail=f"Asset '{asset_id}' missing required field: asset_info.bindings.target_profile_ids[0]"
            )
        
        # Resolve subscribers from policy (raises HTTPException on errors)
        subscribers = await resolve_policy_subscribers(policy_data, personnel_data, asset)
        
        # Resolve safety labels from profile (raises HTTPException on errors)
        safety_labels = await resolve_profile_safety(profile_data, asset)
        
        # Extract camera info
        camera_info = asset.get("asset_info", {}).get("camera", {})
        stream = camera_info.get("stream", {})
        
        # Extract connection details
        rtsp_url = stream.get("rtsp_url", "")
        onvif_url = stream.get("onvif_url", "")
        ip, port = AssetToSensorMapper.extract_ip_port_from_url(onvif_url or rtsp_url)
        
        # Get credentials from camera_info or extract from URL
        username = camera_info.get("userid")
        password = camera_info.get("password")
        
        if not username or not password:
            url_username, url_password = AssetToSensorMapper.extract_credentials_from_url(rtsp_url)
            username = username or url_username
            password = password or url_password
        
        # Build sensor details
        sensor_details = SensorDetails(
            ip=ip,
            port=port,
            username=username,
            password=password,
            uuid=asset["_id"],  # Use asset ID as UUID
            onvif_url=onvif_url
        )
        
        # Build alert rule
        alert_rule = AlertRule(
            alert_type="videosur",
            safety=safety_labels,
            subscribers=subscribers
        )
        
        # Use primary_subscriber_id if provided, otherwise use first subscriber's phone
        if primary_subscriber_id:
            subscriber_id = primary_subscriber_id
        else:
            subscriber_id = subscribers[0].subscriber_id if subscribers else "+000000000"
        
        # Build sensor model
        sensor = SensorModel(
            _id=asset["_id"],  # Use asset ID
            sensor_id=asset["_id"],
            subscriber_id=subscriber_id,
            sensor_type=settings.DEFAULT_SENSOR_TYPE,
            camera_type=settings.DEFAULT_CAMERA_TYPE,
            name=asset.get("name", "Unknown Camera"),
            DOR=datetime.now().strftime("%m-%d-%Y"),
            sensor_details=sensor_details,
            alert_rule=alert_rule,
            description="",
            unit=""
        )
        
        logger.info(
            f"Mapped asset to sensor: {asset_id}",
            extra={
                "asset_id": asset_id,
                "policy_id": policy_id,
                "profile_id": profile_id,
                "subscriber_count": len(subscribers),
                "safety_count": len(safety_labels),
                "primary_subscriber_id": subscriber_id
            }
        )
        
        return sensor
