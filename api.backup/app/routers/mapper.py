from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.config import settings
from app.db import get_db
from app.edge_ai_client import get_edge_ai_client, EdgeAIClient
from app.mapper.schemas import (
    MapAssetRequest, MapAssetResponse, 
    CreateSubscriberRequest, CreateSubscriberResponse,
    DeleteSubscriberRequest, DeleteSubscriberResponse,
    DeleteCameraRequest, DeleteCameraResponse,
    DisablePPERequest, DisablePPEResponse,
    MapperConfigRequest
)
from app.mapper.asset_mapper import AssetToSensorMapper
from app.mapper.personnel_mapper import PersonnelToSubscriberMapper
from app.mapper.edge_ai_transforms import subscriber_to_edge_ai_payload, sensor_to_edge_ai_payload

router = APIRouter(prefix="/api", tags=["mapper"])


@router.post("/configure")
async def configure_mapper(
    request: MapperConfigRequest,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Configure the HMI Mapper to use a specific Gateway's Edge AI credentials.
    
    This switches the context for all subsequent mapper operations.
    
    Args:
        request: MapperConfigRequest with gateway_id
        
    Raises:
        HTTPException(404): Gateway not found
        HTTPException(400): Gateway missing required HMI credentials
    """
    gateway_id = request.gateway_id
    print(f"🔄 Configuring mapper for gateway: {gateway_id}")
    
    # 1. Fetch Gateway details
    gateway = await db["gateway"].find_one({"_id": gateway_id})
    if not gateway:
        raise HTTPException(status_code=404, detail=f"Gateway '{gateway_id}' not found")
    
    hmi_config = gateway.get("hmi", {})
    base_url = hmi_config.get("base_url")
    user_id = hmi_config.get("user_id")
    password = hmi_config.get("password")
    
    # 2. Validate credentials
    if not base_url:
        raise HTTPException(status_code=400, detail=f"Gateway '{gateway_id}' missing hmi.base_url")
    
    # Use defaults if not provided in gateway, or fallback to settings
    # But ideally, if switching context, we strictly want what's in the gateway?
    # For backward compatibility, if user/pass missing in gateway, maybe fall back to settings?
    # User request implies "retrive base_url, user_id and password" from gateway.
    
    final_user_id = user_id or settings.EDGE_AI_USER_ID
    final_password = password or settings.EDGE_AI_PASSWORD
    
    # 3. Reconfigure EdgeAIClient
    try:
        edge_ai = await get_edge_ai_client(base_url, final_user_id, final_password) # Get singleton
        await edge_ai.configure(base_url, final_user_id, final_password)
        print(f"✓ Mapper configured for gateway {gateway_id} ({base_url})")
        return {"success": True, "message": f"Mapper configured for gateway '{gateway_id}'"}
    except Exception as e:
        print(f"❌ Error configuring mapper: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/map-asset", response_model=MapAssetResponse)
async def map_asset(
    request: MapAssetRequest
):
    """
    Map HMI asset to legacy DT_ConfigStorage format and create subscribers
    
    Process:
    1. Extract asset, policy, profile, and personnel data from request
    2. Generate new primary subscriber with tel prefix
    3. Create primary subscriber via Edge AI API
    4. Transform asset to sensor using provided data
    5. Create sensor via Edge AI API (handles DT_ConfigStorage, Cameras/Registered, Util/Cameras)
    
    Args:
        request: MapAssetRequest with asset_data, policy_data, profile_data, personnel_data
        
    Returns:
        MapAssetResponse with success status and created sensor ID
        
    Raises:
        HTTPException(400): Missing required bindings or fields
        HTTPException(404): Policy/profile/personnel not found in provided data
    """
    try:
        # Get Edge AI client
        edge_ai = await get_edge_ai_client(
            settings.EDGE_AI_API_URL,
            settings.EDGE_AI_USER_ID,
            settings.EDGE_AI_PASSWORD
        )
        
        # Extract data from request
        asset = request.asset_data
        policy_data = request.policy_data
        profile_data = request.profile_data
        personnel_data = request.personnel_data
        
        asset_id = asset.get("_id", "UNKNOWN")
        print(f"✓ Processing asset: {asset_id}")
        
        # 2. Generate new primary subscriber with tel prefix
        primary_subscriber_tel = PersonnelToSubscriberMapper.generate_tel_number()
        
        # 3. Create primary subscriber via Edge AI API
        primary_subscriber_payload = subscriber_to_edge_ai_payload(
            subscriber_id=primary_subscriber_tel,
            user_name="Primary Subscriber"
        )
        await edge_ai.add_subscriber(primary_subscriber_payload)
        print(f"✓ Created primary subscriber via Edge AI API: {primary_subscriber_tel}")
        
        # 4. Transform asset to sensor (using provided data)
        sensor = await AssetToSensorMapper.map_asset_to_sensor(
            asset,
            policy_data,
            profile_data,
            personnel_data,
            primary_subscriber_id=primary_subscriber_tel
        )
        
        # Collect all subscriber IDs
        subscriber_ids = [primary_subscriber_tel]
        for alert_subscriber in sensor.alert_rule.subscribers:
            subscriber_ids.append(alert_subscriber.subscriber_id)
        
        # 5. Create sensor via Edge AI API
        # This handles DT_ConfigStorage/sensors, Cameras/Registered, and Util/Cameras
        sensor_payload = sensor_to_edge_ai_payload(sensor)
        await edge_ai.add_sensor(sensor_payload)
        print(f"✓ Created sensor via Edge AI API: {sensor.id}")
        
        return MapAssetResponse(
            success=True,
            sensor_id=sensor.id,
            subscriber_ids=subscriber_ids
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error mapping asset: {str(e)}")
        import traceback
        traceback.print_exc()
        return MapAssetResponse(
            success=False,
            error=str(e)
        )


@router.post("/create-subscriber", response_model=CreateSubscriberResponse)
async def create_subscriber(
    request: CreateSubscriberRequest
):
    """
    Create a subscriber via Edge AI API from personnel data
    
    Process:
    1. Extract personnel data from request
    2. Extract phone number from personnel.contact.phone
    3. Create subscriber via Edge AI API
    
    Args:
        request: CreateSubscriberRequest with personnel_data
        
    Returns:
        CreateSubscriberResponse with success status and subscriber ID
        
    Raises:
        HTTPException(400): Missing contact.phone field
    """
    try:
        # Get Edge AI client
        edge_ai = await get_edge_ai_client(
            settings.EDGE_AI_API_URL,
            settings.EDGE_AI_USER_ID,
            settings.EDGE_AI_PASSWORD
        )
        
        # Extract personnel data from request
        personnel = request.personnel_data
        personnel_id = personnel.get("_id", request.personnel_id or "UNKNOWN")
        
        print(f"✓ Processing personnel: {personnel_id}")
        
        # Extract phone number from personnel.contact.phone
        phone = personnel.get("contact", {}).get("phone")
        if not phone:
            raise HTTPException(
                status_code=400,
                detail=f"Personnel '{personnel_id}' missing required field: contact.phone"
            )
        
        print(f"✓ Extracted phone: {phone}")
        
        # Create subscriber via Edge AI API
        user_name = personnel.get("name", "Unknown")
        subscriber_payload = subscriber_to_edge_ai_payload(
            subscriber_id=phone,
            user_name=user_name
        )
        await edge_ai.add_subscriber(subscriber_payload)
        
        print(f"✓ Created subscriber via Edge AI API: {phone}")
        
        return CreateSubscriberResponse(
            success=True,
            subscriber_id=phone,
            personnel_id=personnel_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating subscriber: {str(e)}")
        import traceback
        traceback.print_exc()
        return CreateSubscriberResponse(
            success=False,
            error=str(e)
        )


@router.post("/delete-subscriber", response_model=DeleteSubscriberResponse)
async def delete_subscriber(
    request: DeleteSubscriberRequest
):
    """
    Delete a subscriber via Edge AI API based on personnel data
    
    Process:
    1. Extract personnel data from request
    2. Extract phone number from personnel.contact.phone
    3. Delete subscriber via Edge AI API
    
    Args:
        request: DeleteSubscriberRequest with personnel_data
        
    Returns:
        DeleteSubscriberResponse with success status and subscriber ID
        
    Raises:
        HTTPException(400): Missing contact.phone field
    """
    try:
        # Get Edge AI client
        edge_ai = await get_edge_ai_client(
            settings.EDGE_AI_API_URL,
            settings.EDGE_AI_USER_ID,
            settings.EDGE_AI_PASSWORD
        )
        
        # Extract personnel data from request
        personnel = request.personnel_data
        personnel_id = personnel.get("_id", request.personnel_id or "UNKNOWN")
        
        print(f"✓ Processing personnel: {personnel_id}")
        
        # Extract phone number from personnel.contact.phone
        phone = personnel.get("contact", {}).get("phone")
        if not phone:
            raise HTTPException(
                status_code=400,
                detail=f"Personnel '{personnel_id}' missing required field: contact.phone"
            )
        
        print(f"✓ Extracted phone: {phone}")
        
        # Delete subscriber via Edge AI API
        await edge_ai.delete_subscriber(phone)
        print(f"✓ Deleted subscriber via Edge AI API: {phone}")
        
        return DeleteSubscriberResponse(
            success=True,
            subscriber_id=phone,
            personnel_id=personnel_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting subscriber: {str(e)}")
        import traceback
        traceback.print_exc()
        return DeleteSubscriberResponse(
            success=False,
            error=str(e)
        )


@router.post("/delete-camera", response_model=DeleteCameraResponse)
async def delete_camera(
    request: DeleteCameraRequest
):
    """
    Delete a camera sensor and its primary subscriber via Edge AI API
    
    Process:
    1. Fetch sensor details to get subscriber_id
    2. Delete primary subscriber [subscriber associated with camera] (additionally check if it has the tel prefix)
    3. Delete sensor from all collections
    
    The Edge AI API handles sensor deletion from:
    - DT_ConfigStorage/sensors
    - Cameras/Registered
    - Util/Cameras
    
    Args:
        request: DeleteCameraRequest with camera_id
        
    Returns:
        DeleteCameraResponse with success status
    """
    try:
        # Get Edge AI client
        edge_ai = await get_edge_ai_client(
            settings.EDGE_AI_API_URL,
            settings.EDGE_AI_USER_ID,
            settings.EDGE_AI_PASSWORD
        )
        
        camera_id = request.camera_id
        
        # Step 1: Fetch sensor details to get subscriber_id
        try:
            sensor_response = await edge_ai.get_sensor(camera_id)
            #print(f"✓ Fetched sensor response: {sensor_response}")
            
            # Extract sensor data from 'message' field if present
            sensor_details = sensor_response.get("message", sensor_response)
            subscriber_id = sensor_details.get("subscriber_id")
            #print(f"✓ Extracted subscriber_id: {subscriber_id}")
            
            # Step 2: Delete primary subscriber [subscriber associated with camera]
            if subscriber_id:
                try:
                    await edge_ai.delete_subscriber(subscriber_id)
                    print(f"✓ Deleted primary subscriber via Edge AI API: {subscriber_id}")
                except Exception as e:
                    print(f"⚠ Failed to delete subscriber {subscriber_id}: {e}")
                    # Continue with sensor deletion even if subscriber deletion fails
            else:
                print(f"⚠ No subscriber_id found in sensor details")
        except Exception as e:
            print(f"⚠ Failed to fetch sensor details: {e}")
            # Continue with sensor deletion even if we can't get details
        
        # Step 3: Delete sensor via Edge AI API
        await edge_ai.delete_sensor(camera_id)
        print(f"✓ Deleted sensor via Edge AI API: {camera_id}")
        
        return DeleteCameraResponse(
            success=True,
            camera_id=camera_id,
            deleted_from=["DT_ConfigStorage/sensors", "Cameras/Registered", "Util/Cameras", "Primary Subscriber"]
        )
    
    except Exception as e:
        print(f"❌ Error deleting camera: {str(e)}")
        import traceback
        traceback.print_exc()
        return DeleteCameraResponse(
            success=False,
            camera_id=request.camera_id,
            deleted_from=[],
            error=str(e)
        )


@router.post("/disable-ppe", response_model=DisablePPEResponse)
async def disable_ppe(
    request: DisablePPERequest
):
    """
    Disable PPE monitoring for a camera by setting status to INACTIVE and cleaning up legacy data
    
    Process:
    1. Fetch sensor details to get subscriber_id
    2. Delete primary subscriber via Edge AI API
    3. Delete sensor from all collections via Edge AI API
    
    The Edge AI API handles sensor deletion from:
    - DT_ConfigStorage/sensors
    - Cameras/Registered
    - Util/Cameras
    
    Note: This does NOT delete the camera from HMI database.
    The camera status should be updated to INACTIVE by the caller (MCP tool).
    
    Args:
        request: DisablePPERequest with camera_id
        
    Returns:
        DisablePPEResponse with success status
    """
    try:
        # Get Edge AI client
        edge_ai = await get_edge_ai_client(
            settings.EDGE_AI_API_URL,
            settings.EDGE_AI_USER_ID,
            settings.EDGE_AI_PASSWORD
        )
        
        camera_id = request.camera_id
        
        # Step 1: Fetch sensor details to get subscriber_id
        try:
            sensor_response = await edge_ai.get_sensor(camera_id)
            
            # Extract sensor data from 'message' field if present
            sensor_details = sensor_response.get("message", sensor_response)
            subscriber_id = sensor_details.get("subscriber_id")
            
            # Step 2: Delete primary subscriber
            if subscriber_id:
                try:
                    await edge_ai.delete_subscriber(subscriber_id)
                    print(f"✓ Deleted primary subscriber via Edge AI API: {subscriber_id}")
                except Exception as e:
                    print(f"⚠ Failed to delete subscriber {subscriber_id}: {e}")
                    # Continue with sensor deletion even if subscriber deletion fails
            else:
                print(f"⚠ No subscriber_id found in sensor details")
        except Exception as e:
            print(f"⚠ Failed to fetch sensor details: {e}")
            # Continue with sensor deletion even if we can't get details
        
        # Step 3: Delete sensor via Edge AI API
        await edge_ai.delete_sensor(camera_id)
        print(f"✓ Deleted sensor via Edge AI API: {camera_id}")
        
        return DisablePPEResponse(
            success=True,
            camera_id=camera_id,
            deleted_from=["DT_ConfigStorage/sensors", "Cameras/Registered", "Util/Cameras", "Primary Subscriber"]
        )
    
    except Exception as e:
        print(f"❌ Error disabling PPE for camera: {str(e)}")
        import traceback
        traceback.print_exc()
        return DisablePPEResponse(
            success=False,
            camera_id=request.camera_id,
            deleted_from=[],
            error=str(e)
        )

