# mcp_server/tools/debug.py
#from fastmcp import tool
from typing import Dict, Any, Optional
from mcp_server.server import mcp

from mcp_server.data_store import (
    MOCK_ASSETS,
    MOCK_DETECTION_PROFILES,
    MOCK_MODELS,
    MOCK_PERSONNEL,
    MOCK_ALERT_POLICIES,
)


@mcp.tool()
async def debug_state(
    tenant_id: Optional[str] = None,
    include_cameras: bool = True,
    include_profiles: bool = True,
    include_models: bool = True,
    include_personnel: bool = True,
    include_policies: bool = True,
) -> Dict[str, Any]:
    """
    Debug tool: dump current in-memory state for inspection.

    NOTE:
    - This is for dev/test only, not for production.
    - Optionally filters by tenant_id where applicable.
    """
    state: Dict[str, Any] = {}

    if include_cameras:
        cams = MOCK_ASSETS
        if tenant_id:
            cams = [c for c in cams if c.get("tenant_id") == tenant_id]
        state["cameras"] = cams

    if include_profiles:
        profiles = MOCK_DETECTION_PROFILES
        if tenant_id:
            profiles = [p for p in profiles if p.get("tenant_id") == tenant_id]
        state["detection_profiles"] = profiles

    if include_models:
        models = MOCK_MODELS
        if tenant_id:
            models = [m for m in models if m.get("tenant_id") == tenant_id]
        state["models"] = models

    if include_personnel:
        people = MOCK_PERSONNEL
        if tenant_id:
            people = [p for p in people if p.get("tenant_id") == tenant_id]
        state["personnel"] = people

    if include_policies:
        policies = MOCK_ALERT_POLICIES
        if tenant_id:
            policies = [p for p in policies if p.get("tenant_id") == tenant_id]
        state["alert_policies"] = policies

    return state
