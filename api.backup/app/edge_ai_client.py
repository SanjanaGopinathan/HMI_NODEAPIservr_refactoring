"""
IOTA-E (Edge AI) API Client

Wrapper client for IOTA-E legacy API with authentication and session management.
Replaces direct MongoDB access with API calls.
"""

import httpx
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class EdgeAIClient:
    """Client for IOTA-E Edge AI API with session management"""
    
    def __init__(self, base_url: str, user_id: str, password: str, timeout: float = 60.0):
        """
        Initialize Edge AI client
        
        Args:
            base_url: Base URL of Edge AI API (e.g., http://106.51.182.207:30019)
            user_id: Username for authentication
            password: Password for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.user_id = user_id
        self.password = password
        self.timeout = httpx.Timeout(timeout)
        self.session_cookie: Optional[str] = None
        
    async def _login(self) -> None:
        """
        Login to Edge AI API and store session cookie
        
        Raises:
            httpx.HTTPError: If login fails
        """
        url = f"{self.base_url}/login"
        
        payload = {
            "userId": self.user_id,
            "password": self.password
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        logger.info(f"Logging in to Edge AI API as '{self.user_id}'")
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            # Store session cookie
            if 'iotae.sid' in response.cookies:
                self.session_cookie = response.cookies['iotae.sid']
                logger.info("Login successful, session cookie obtained")
            else:
                logger.warning("Login response received but no session cookie found")
                raise RuntimeError("No session cookie received from Edge AI API")
    
    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid session, login if needed"""
        if not self.session_cookie:
            await self._login()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """
        Make authenticated request to Edge AI API with auto re-authentication
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/api/subscriber")
            params: Query parameters
            json: JSON payload
            
        Returns:
            HTTP response
            
        Raises:
            httpx.HTTPError: If request fails after re-authentication
        """
        await self._ensure_authenticated()
        
        url = f"{self.base_url}{endpoint}"
        cookies = {"iotae.sid": self.session_cookie}
        headers = {"Content-Type": "application/json"}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method,
                url,
                params=params,
                json=json,
                cookies=cookies,
                headers=headers
            )
            
            # Auto re-authenticate on 401
            if response.status_code == 401:
                logger.warning("Session expired (401), re-authenticating...")
                await self._login()
                cookies = {"iotae.sid": self.session_cookie}
                
                response = await client.request(
                    method,
                    url,
                    params=params,
                    json=json,
                    cookies=cookies,
                    headers=headers
                )
            
            response.raise_for_status()
            return response
    
    async def add_subscriber(self, subscriber_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add subscriber to user-data collection
        
        Args:
            subscriber_data: Subscriber payload with subscriberId, password, userInfo, service
            
        Returns:
            Response from Edge AI API
            
        Example payload:
            {
                "subscriberId": "+919880000002",
                "password": "ecrio@123",
                "userInfo": {
                    "userName": "John Doe",
                    "dor": "19-01-2026",
                    "org": "ecrio.com"
                },
                "service": {
                    "comms": [{"isBlocked": false}]
                }
            }
        """
        logger.info(f"Adding subscriber: {subscriber_data.get('subscriberId')}")
        
        response = await self._request(
            "POST",
            "/api/subscriber",
            params={"action": "add"},
            json=subscriber_data
        )
        
        logger.info(f"Subscriber added successfully: {subscriber_data.get('subscriberId')}")
        return response.json()
    
    async def delete_subscriber(self, subscriber_id: str) -> Dict[str, Any]:
        """
        Delete subscriber from user-data collection
        
        Args:
            subscriber_id: Subscriber ID (phone number)
            
        Returns:
            Response from Edge AI API
        """
        logger.info(f"Deleting subscriber: {subscriber_id}")
        
        payload = {"subscriberId": subscriber_id}
        
        response = await self._request(
            "POST",
            "/api/subscriber",
            params={"action": "delete"},
            json=payload
        )
        
        logger.info(f"Subscriber deleted successfully: {subscriber_id}")
        return response.json()
    
    async def add_sensor(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add sensor to DT_ConfigStorage and related collections
        
        The Edge AI API handles:
        - DT_ConfigStorage/sensors
        - Cameras/Registered
        - Util/Cameras
        
        Args:
            sensor_data: Sensor payload (SensorModel dict)
            
        Returns:
            Response from Edge AI API
        """
        sensor_id = sensor_data.get('sensor_id', 'UNKNOWN')
        logger.info(f"Adding sensor: {sensor_id}")
        
        response = await self._request(
            "POST",
            "/api/sensor",
            params={"action": "add"},
            json=sensor_data
        )
        
        logger.info(f"Sensor added successfully: {sensor_id}")
        return response.json()
    
    async def get_sensor(self, sensor_id: str) -> Dict[str, Any]:
        """
        Get sensor details from DT_ConfigStorage
        
        Args:
            sensor_id: Sensor ID to retrieve
            
        Returns:
            Sensor data from Edge AI API
        """
        logger.info(f"Getting sensor details: {sensor_id}")
        payload = {"sensor_id": sensor_id}
        
        response = await self._request(
            "POST",
            "/api/sensor",
            params={"action": "view"},
            json=payload
        )
        
        logger.info(f"Sensor details retrieved: {response.json()}")
        return response.json()
    
    async def delete_sensor(self, sensor_id: str) -> Dict[str, Any]:
        """
        Delete sensor from all collections
        
        The Edge AI API handles deletion from:
        - DT_ConfigStorage/sensors
        - Cameras/Registered
        - Util/Cameras
        
        Args:
            sensor_id: Sensor ID to delete
            
        Returns:
            Response from Edge AI API
        """
        logger.info(f"Deleting sensor: {sensor_id}")
        
        payload = {"sensor_id": sensor_id}
        
        response = await self._request(
            "POST",
            "/api/sensor",
            params={"action": "delete"},
            json=payload
        )
        
        logger.info(f"Sensor deleted successfully: {sensor_id}")
        return response.json()


    async def configure(self, base_url: str, user_id: str, password: str) -> None:
        """
        Reconfigure the client with new credentials and reset session
        
        Args:
            base_url: New Base URL
            user_id: New Username
            password: New Password
        """
        new_base_url = base_url.rstrip('/')

        # Optimization: Check if configuration is identical to avoid unnecessary re-login
        if (self.base_url == new_base_url and 
            self.user_id == user_id and 
            self.password == password and 
            self.session_cookie is not None): # Ensure we actually have a session
            logger.info("Edge AI Client configuration unchanged, reusing existing session.")
            return

        logger.info(f"Reconfiguring Edge AI Client for user: {user_id} at {base_url}")
        self.base_url = new_base_url
        self.user_id = user_id
        self.password = password
        self.session_cookie = None
        await self._login()


# Global singleton instance (initialized on first use)
_edge_ai_client: Optional[EdgeAIClient] = None


async def get_edge_ai_client(
    base_url: str | None = None,
    user_id: str | None = None,
    password: str | None = None
) -> EdgeAIClient:
    """
    Get or create Edge AI client singleton.
    
    If params are provided, they are used for INITIALIZATION only.
    To reconfigure an existing client, use client.configure().
    
    Args:
        base_url: Edge AI API base URL
        user_id: Username
        password: Password
        
    Returns:
        Initialized and authenticated EdgeAIClient
    """
    global _edge_ai_client
    
    if _edge_ai_client is None:
        if not base_url or not user_id or not password:
             raise ValueError("Initial EdgeAIClient creation requires base_url, user_id, and password")
             
        _edge_ai_client = EdgeAIClient(base_url, user_id, password)
        await _edge_ai_client._login()
    
    return _edge_ai_client
