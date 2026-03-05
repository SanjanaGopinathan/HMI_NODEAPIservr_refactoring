# mcp_server/hmi_mapper_client.py
"""
Client for HMI Mapper FastAPI service
"""
import httpx
from typing import Dict, Any, Optional
from mcp_server.config import settings


class HMIMapperClient:
    """Client for interacting with HMI Mapper service"""
    
    def __init__(self, base_url: Optional[str] = None, timeout: float = 60.0):
        """
        Initialize HMI Mapper client
        
        Args:
            base_url: Base URL for HMI Mapper service (default: from settings)
            timeout: Request timeout in seconds (default: 60.0)
        """
        self.base_url = base_url or settings.HMI_MAPPER_URL
        self.timeout = httpx.Timeout(timeout)
    
    async def create_subscriber(self, personnel_data: dict) -> Dict[str, Any]:
        """
        Create a subscriber in iota-e/user-data from personnel data
        
        Args:
            personnel_data: Complete personnel document from hmi_db.personnel
            
        Returns:
            Dict containing:
                - success: Boolean indicating success
                - subscriber_id: Created subscriber ID (phone number)
                - personnel_id: Personnel ID
                - error: Error message (if failed)
        """
        url = f"{self.base_url}/api/create-subscriber"
        payload = {"personnel_data": personnel_data}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def delete_subscriber(self, personnel_data: dict) -> Dict[str, Any]:
        """
        Delete a subscriber from iota-e/user-data based on personnel data
        
        Args:
            personnel_data: Complete personnel document from hmi_db.personnel
            
        Returns:
            Dict containing:
                - success: Boolean indicating success
                - subscriber_id: Deleted subscriber ID (phone number)
                - personnel_id: Personnel ID
                - error: Error message (if failed)
        """
        url = f"{self.base_url}/api/delete-subscriber"
        payload = {"personnel_data": personnel_data}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def map_asset(
        self,
        asset_data: dict,
        policy_data: dict,
        profile_data: dict,
        personnel_data: list
    ) -> Dict[str, Any]:
        """
        Map an HMI asset to legacy format
        
        Args:
            asset_data: Complete asset document from hmi_db.assets
            policy_data: Complete policy document from hmi_db.policies
            profile_data: Complete profile document from hmi_db.profiles
            personnel_data: List of personnel documents for all PERSON targets
            
        Returns:
            Dict containing:
                - success: Boolean indicating success
                - sensor_id: Created sensor ID
                - subscriber_ids: List of subscriber IDs
                - error: Error message (if failed)
        """
        url = f"{self.base_url}/api/map-asset"
        payload = {
            "asset_data": asset_data,
            "policy_data": policy_data,
            "profile_data": profile_data,
            "personnel_data": personnel_data
        }
        
        print(f"?? DEBUG: Calling HMI Mapper API")
        print(f"   URL: {url}")
        print(f"   Asset ID: {asset_data.get('_id', 'UNKNOWN')}")
        print(f"   Policy ID: {policy_data.get('_id', 'UNKNOWN')}")
        print(f"   Profile ID: {profile_data.get('_id', 'UNKNOWN')}")
        print(f"   Personnel count: {len(personnel_data)}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                print(f"?? DEBUG: Sending POST request...")
                response = await client.post(url, json=payload)
                print(f"? DEBUG: Got response with status: {response.status_code}")
                response.raise_for_status()
                result = response.json()
                print(f"?? DEBUG: Response data: {result}")
                return result
        except Exception as e:
            print(f"? DEBUG: Exception in map_asset: {type(e).__name__}: {e}")
            raise
    
    async def delete_camera(self, camera_id: str) -> Dict[str, Any]:
        """
        Delete a camera sensor from all collections
        
        Deletes from:
        - DT_ConfigStorage/sensors
        - Cameras/Registered
        - Util/Cameras
        
        Args:
            camera_id: Camera ID to delete
            
        Returns:
            Dict containing:
                - success: Boolean indicating success
                - camera_id: Camera ID
                - deleted_from: List of collections deleted from
                - error: Error message (if failed)
        """
        url = f"{self.base_url}/api/delete-camera"
        payload = {"camera_id": camera_id}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    
    async def disable_ppe(self, camera_id: str) -> Dict[str, Any]:
        """
        Disable PPE monitoring for a camera
        
        This cleans up legacy sensor and subscriber data without deleting
        the camera from HMI database.
        
        Args:
            camera_id: Camera ID to disable PPE for
            
        Returns:
            Dict containing:
                - success: Boolean indicating success
                - camera_id: Camera ID
                - deleted_from: List of collections deleted from
                - error: Error message (if failed)
        """
        url = f"{self.base_url}/api/disable-ppe"
        payload = {"camera_id": camera_id}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
    async def configure_mapper(self, gateway_id: str) -> Dict[str, Any]:
        """
        Configure the HMI Mapper to use a specific Gateway's credentials.
        
        Args:
            gateway_id: Gateway ID to switch context to
            
        Returns:
            Response from HMI Mapper API
        """
        url = f"{self.base_url}/api/configure"
        payload = {"gateway_id": gateway_id}
        
        print(f"?? DEBUG: Configuring HMI Mapper for gateway: {gateway_id}")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()


# Singleton instance
hmi_mapper_client = HMIMapperClient()

