# mcp_server/tools/models.py
#from fastmcp import tool
from typing import Dict, Any, Optional, List
from mcp_server.data_store import MOCK_MODELS, MOCK_CAMERAS
from mcp_server.server import mcp

@mcp.tool()
async def list_models(
    tenant_id: str,
    framework_id: Optional[str] = None,
    status: str = "ACTIVE",
) -> Dict[str, Any]:
    """
    List CV models from canned data.
    """
    models = [
        m for m in MOCK_MODELS
        if m["tenant_id"] == tenant_id
    ]

    if framework_id:
        models = [m for m in models if m["framework_id"] == framework_id]
    if status:
        models = [m for m in models if m.get("status") == status]

    return {"models": models}


@mcp.tool()
async def assign_cameras_to_model(
    tenant_id: str,
    camera_ids: List[str],
    model_id: str,
    auto_adjust_stream_profile: bool = True,
) -> Dict[str, Any]:
    """
    Assign cameras to the given model (in-memory).
    """
    assigned = []

    for cam in MOCK_CAMERAS:
        if cam["tenant_id"] != tenant_id:
            continue
        if cam["_id"] not in camera_ids:
            continue
        cam["assigned_cv_model_id"] = model_id
        assigned.append(cam["_id"])

    return {
        "status": "ok",
        "assigned_camera_ids": assigned,
        "model_id": model_id,
        "auto_adjust_stream_profile": auto_adjust_stream_profile,
    }
