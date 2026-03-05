from typing import Any
from mcp.server.fastmcp import FastMCP, Context
from mcp_server.hmi_mapper_client import hmi_mapper_client
from mcp_server.server import mcp

@mcp.tool()
async def configure_mapper(gateway_id: str) -> dict:
    """
    Configure the HMI Mapper to use a specific Gateway's credentials.
    
    Args:
        gateway_id: Gateway ID to switch context to
    """
    try:
        return await hmi_mapper_client.configure_mapper(gateway_id)
    except Exception as e:
        return {"error": str(e), "success": False}
