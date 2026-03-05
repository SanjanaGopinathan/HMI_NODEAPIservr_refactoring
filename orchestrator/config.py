# orchestrator/config.py
"""
Configuration for Orchestrator
"""
from config_loader import config


# MCP Server connection
MCP_SERVER_URL = config.get(
    "orchestrator", "mcp_server_url",
    default="http://127.0.0.1:8001/mcp-server/mcp",
    env_var="MCP_SERVER_URL"
)

# Orchestrator API settings
ORCHESTRATOR_HOST = config.get(
    "orchestrator", "host",
    default="0.0.0.0",
    env_var="ORCHESTRATOR_HOST"
)

ORCHESTRATOR_PORT = config.get_int(
    "orchestrator", "port",
    default=8020,
    env_var="ORCHESTRATOR_PORT"
)

# Default tenant/site/gateway IDs
DEFAULT_TENANT_ID = config.get(
    "orchestrator", "default_tenant_id",
    default="TENANT_01",
    env_var="DEFAULT_TENANT_ID"
)

DEFAULT_SITE_ID = config.get(
    "orchestrator", "default_site_id",
    default="SITE_01",
    env_var="DEFAULT_SITE_ID"
)

DEFAULT_GATEWAY_ID = config.get(
    "orchestrator", "default_gateway_id",
    default=None,  # Don't filter by gateway by default - allow all gateways
    env_var="DEFAULT_GATEWAY_ID"
)


# Runtime configuration manager
class RuntimeConfig:
    """
    Manages runtime configuration that can be updated without restarting.
    Thread-safe for concurrent access.
    
    Features:
    - Static defaults (from config file)
    - Runtime defaults (can be updated via API)
    - Last-used values (sticky behavior - remembers last explicitly provided values)
    """
    _instance = None
    _lock = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize with config file/env defaults
            cls._instance._tenant_id = DEFAULT_TENANT_ID
            cls._instance._site_id = DEFAULT_SITE_ID
            cls._instance._gateway_id = DEFAULT_GATEWAY_ID
            
            # Track last-used values (for sticky behavior)
            cls._instance._last_tenant_id = None
            cls._instance._last_site_id = None
            cls._instance._last_gateway_id = None
            
            # Import threading here to avoid circular imports
            import threading
            cls._lock = threading.Lock()
        return cls._instance
    
    @property
    def tenant_id(self) -> str:
        """Get current default tenant ID"""
        with self._lock:
            return self._tenant_id
    
    @tenant_id.setter
    def tenant_id(self, value: str):
        """Set default tenant ID"""
        with self._lock:
            self._tenant_id = value
    
    @property
    def site_id(self) -> str:
        """Get current default site ID"""
        with self._lock:
            return self._site_id
    
    @site_id.setter
    def site_id(self, value: str):
        """Set default site ID"""
        with self._lock:
            self._site_id = value
    
    @property
    def gateway_id(self) -> str:
        """Get current default gateway ID"""
        with self._lock:
            return self._gateway_id
    
    @gateway_id.setter
    def gateway_id(self, value: str):
        """Set default gateway ID"""
        with self._lock:
            self._gateway_id = value
    
    def update(self, tenant_id: str = None, site_id: str = None, gateway_id: str = None):
        """Update one or more default values"""
        with self._lock:
            if tenant_id is not None:
                self._tenant_id = tenant_id
            if site_id is not None:
                self._site_id = site_id
            if gateway_id is not None:
                self._gateway_id = gateway_id
    
    def update_last_used(self, tenant_id: str = None, site_id: str = None, gateway_id: str = None):
        """Update last-used values (called when explicit values are provided)"""
        with self._lock:
            if tenant_id is not None:
                self._last_tenant_id = tenant_id
            if site_id is not None:
                self._last_site_id = site_id
            if gateway_id is not None:
                self._last_gateway_id = gateway_id
    
    def get_effective_defaults(self, use_last_used: bool = True) -> dict:
        """
        Get effective defaults, optionally using last-used values.
        
        Priority (when use_last_used=True):
        1. Last-used value (if available)
        2. Runtime default
        
        Args:
            use_last_used: If True, prefer last-used values over runtime defaults
        """
        with self._lock:
            if use_last_used:
                return {
                    "tenant_id": self._last_tenant_id or self._tenant_id,
                    "site_id": self._last_site_id or self._site_id,
                    "gateway_id": self._last_gateway_id or self._gateway_id,
                }
            else:
                return {
                    "tenant_id": self._tenant_id,
                    "site_id": self._site_id,
                    "gateway_id": self._gateway_id,
                }
    
    def get_all(self) -> dict:
        """Get all current defaults"""
        with self._lock:
            return {
                "tenant_id": self._tenant_id,
                "site_id": self._site_id,
                "gateway_id": self._gateway_id,
            }
    
    def get_last_used(self) -> dict:
        """Get last-used values"""
        with self._lock:
            return {
                "tenant_id": self._last_tenant_id,
                "site_id": self._last_site_id,
                "gateway_id": self._last_gateway_id,
            }
    
    def clear_last_used(self):
        """Clear last-used values"""
        with self._lock:
            self._last_tenant_id = None
            self._last_site_id = None
            self._last_gateway_id = None
    
    def reset_to_config(self):
        """Reset to original config file/env defaults"""
        with self._lock:
            self._tenant_id = DEFAULT_TENANT_ID
            self._site_id = DEFAULT_SITE_ID
            self._gateway_id = DEFAULT_GATEWAY_ID
            # Also clear last-used values
            self._last_tenant_id = None
            self._last_site_id = None
            self._last_gateway_id = None



# Global runtime config instance
runtime_config = RuntimeConfig()


# Helper functions for easy access
def get_current_tenant_id(use_last_used: bool = True) -> str:
    """
    Get current runtime default tenant ID.
    
    Args:
        use_last_used: If True, prefer last explicitly provided value
    """
    defaults = runtime_config.get_effective_defaults(use_last_used=use_last_used)
    return defaults["tenant_id"]


def get_current_site_id(use_last_used: bool = True) -> str:
    """
    Get current runtime default site ID.
    
    Args:
        use_last_used: If True, prefer last explicitly provided value
    """
    defaults = runtime_config.get_effective_defaults(use_last_used=use_last_used)
    return defaults["site_id"]


def get_current_gateway_id(use_last_used: bool = True) -> str:
    """
    Get current runtime default gateway ID.
    
    Args:
        use_last_used: If True, prefer last explicitly provided value
    """
    defaults = runtime_config.get_effective_defaults(use_last_used=use_last_used)
    return defaults["gateway_id"]


def update_defaults(tenant_id: str = None, site_id: str = None, gateway_id: str = None):
    """Update runtime defaults"""
    runtime_config.update(tenant_id=tenant_id, site_id=site_id, gateway_id=gateway_id)


def update_last_used(tenant_id: str = None, site_id: str = None, gateway_id: str = None):
    """Update last-used values (sticky defaults)"""
    runtime_config.update_last_used(tenant_id=tenant_id, site_id=site_id, gateway_id=gateway_id)


def get_all_defaults() -> dict:
    """Get all current runtime defaults"""
    return runtime_config.get_all()


def get_last_used() -> dict:
    """Get last-used values"""
    return runtime_config.get_last_used()


def get_effective_defaults(use_last_used: bool = True) -> dict:
    """
    Get effective defaults with optional sticky behavior.
    
    Args:
        use_last_used: If True, prefer last explicitly provided values
    """
    return runtime_config.get_effective_defaults(use_last_used=use_last_used)


def clear_last_used():
    """Clear last-used values"""
    runtime_config.clear_last_used()


def reset_defaults():
    """Reset to original config file defaults"""
    runtime_config.reset_to_config()

