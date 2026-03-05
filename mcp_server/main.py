# mcp_server/main.py
from fastapi import FastAPI
from mcp_server.server import mcp

# Import tools so their @mcp.tool decorators run and register them
from mcp_server.tools import (
    sensors_camera,
    profiles,
    ai_models,
    alerts_policies,
    personnel,
    anomaly,
    debug,
    query,  # New query tools
    config_tool, # Config tool
)

# Create MCP ASGI app (Streamable HTTP transport under /mcp)
mcp_app = mcp.http_app(path="/mcp")  # MCP endpoint will be .../mcp

# Main FastAPI app, using MCP lifespan
app = FastAPI(
    title="HMI MCP Server",
    lifespan=mcp_app.lifespan,
)

# Mount MCP under /mcp-server → final MCP endpoint = /mcp-server/mcp
app.mount("/mcp-server", mcp_app)


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "component": "mcp_server"}
