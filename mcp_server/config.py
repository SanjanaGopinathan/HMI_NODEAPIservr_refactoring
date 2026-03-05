# mcp_server/config.py
"""
Configuration for MCP Server
"""
from config_loader import config


class MCPSettings:
    """MCP Server settings loaded from config.ini and environment variables"""
    
    # API connection settings
    API_BASE_URL: str = config.get(
        "mcp_server", "api_base_url",
        default="http://127.0.0.1:8015",
        env_var="API_BASE_URL"
    )
    
    HMI_MAPPER_URL: str = config.get(
        "mcp_server", "hmi_mapper_url",
        default="http://127.0.0.1:8015",  # Changed to unified API port
        env_var="HMI_MAPPER_URL"
    )
    
    # MCP Server settings
    MCP_HOST: str = config.get(
        "mcp_server", "host",
        default="127.0.0.1",
        env_var="MCP_HOST"
    )
    
    MCP_PORT: int = config.get_int(
        "mcp_server", "port",
        default=8001,
        env_var="MCP_PORT"
    )
    
    # Connection settings
    TIMEOUT: int = config.get_int(
        "mcp_server", "timeout",
        default=60,  # Increased from 30 to 60 seconds
        env_var="MCP_TIMEOUT"
    )
    
    MAX_RETRIES: int = config.get_int(
        "mcp_server", "max_retries",
        default=3,
        env_var="MCP_MAX_RETRIES"
    )


settings = MCPSettings()

