# orchestrator/mcp_client.py
from __future__ import annotations

import os
from typing import Any, Dict

from fastmcp import Client as FastMCPClient


# URL of your MCP HTTP endpoint – matches how you mounted it:
# app.mount("/mcp-server", mcp_app)  ->  /mcp-server/mcp
MCP_SERVER_URL = os.getenv(
    "MCP_SERVER_URL",
    "http://localhost:8001/mcp-server/mcp",
)


class MCPClient:
    """
    Thin wrapper around FastMCP's Client for calling tools
    from the Orchestrator / LangGraph workflows.
    """

    def __init__(self, server_url: str | None = None) -> None:
        self.server_url = server_url or MCP_SERVER_URL

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool and return its structured result as a plain dict.

        - Uses FastMCP Client over HTTP so that:
          * Correct Accept headers are sent (no 406)
          * Full MCP protocol is spoken (initialize, tools/call, etc.)
        """
        client = FastMCPClient(self.server_url)

        async with client:
            # This handles all MCP JSON-RPC & HTTP details for you
            result = await client.call_tool(name, arguments)

        # For tools that return dicts (your case), FastMCP exposes them via `.data`
        data = result.data

        if not isinstance(data, dict):
            # You can relax this later, but for now we enforce dict
            raise TypeError(
                f"Tool '{name}' returned non-dict data: {type(data)} – {data!r}"
            )

        return data
