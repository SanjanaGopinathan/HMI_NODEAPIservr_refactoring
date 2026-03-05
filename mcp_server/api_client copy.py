# mcp_server/api_client.py
"""
HTTP client for calling the FastAPI backend with connection pooling
"""
import httpx
from typing import Dict, Any, Optional
from mcp_server.config import settings


class APIClient:
    """Async HTTP client for FastAPI backend with connection pooling"""
    
    _instance = None
    _client = None
    
    def __new__(cls, base_url: Optional[str] = None):
        """Singleton pattern for connection pooling"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_client(base_url)
        return cls._instance
    
    def _init_client(self, base_url: Optional[str] = None):
        """Initialize the HTTP client with connection pooling"""
        self.base_url = base_url or settings.API_BASE_URL
        self.timeout = httpx.Timeout(30.0)
        # Create a persistent client with connection pooling (limits=httpx.Limits(max_connections=100))
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )
    
    async def get(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a GET request to the API
        
        Args:
            endpoint: API endpoint (e.g., "/assets")
            params: Query parameters
            
        Returns:
            Response JSON as dict
        """
        url = f"{self.base_url}{endpoint}"
        response = await self._client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    async def post(
        self, 
        endpoint: str, 
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a POST request to the API
        
        Args:
            endpoint: API endpoint
            json: Request body as dict
            params: Query parameters
            
        Returns:
            Response JSON as dict
        """
        url = f"{self.base_url}{endpoint}"
        response = await self._client.post(url, json=json, params=params)
        response.raise_for_status()
        return response.json()
    
    async def put(
        self, 
        endpoint: str, 
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a PUT request to the API
        
        Args:
            endpoint: API endpoint
            json: Request body as dict
            params: Query parameters
            
        Returns:
            Response JSON as dict
        """
        url = f"{self.base_url}{endpoint}"
        response = await self._client.put(url, json=json, params=params)
        response.raise_for_status()
        return response.json()
    
    async def delete(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Make a DELETE request to the API
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            True if successful (204 No Content)
        """
        url = f"{self.base_url}{endpoint}"
        response = await self._client.delete(url, params=params)
        response.raise_for_status()
        return response.status_code == 204


# Singleton instance
api_client = APIClient()
