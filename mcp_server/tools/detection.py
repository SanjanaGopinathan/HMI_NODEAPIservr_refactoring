# mcp_server/tools/detection.py
#from fastmcp import tool
from typing import Dict, Any, Optional, List
from mcp_server.data_store import MOCK_DETECTION_PROFILES, MOCK_CAMERAS
from mcp_server.server import mcp

@mcp.tool()
async def list_detection_profiles(
    tenant_id: str,
    target_name_contains: Optional[str] = None,
) -> Dict[str, Any]:
    """
    List detection profiles (targets) from canned data.
    """
    profiles = [
        p for p in MOCK_DETECTION_PROFILES
        if p["tenant_id"] == tenant_id
    ]

    if target_name_contains:
        t = target_name_contains.lower()
        profiles = [p for p in profiles if t in p["name"].lower()]

    return {"detection_profiles": profiles}


@mcp.tool()
async def assign_detection_profile(
    tenant_id: str,
    camera_ids: List[str],
    target_profile_ids: List[str],
    mode: str = "MERGE",
) -> Dict[str, Any]:
    """
    Assign detection profiles to cameras.
    Uses in-memory MOCK_CAMERAS and mutates target_profile_ids.
    """
    updated = []

    for cam in MOCK_CAMERAS:
        if cam["tenant_id"] != tenant_id:
            continue
        if cam["_id"] not in camera_ids:
            continue

        existing = cam.get("target_profile_ids") or []
        if mode == "REPLACE":
            new_profiles = list(dict.fromkeys(target_profile_ids))
        else:  # MERGE
            new_profiles = list(dict.fromkeys(existing + target_profile_ids))

        cam["target_profile_ids"] = new_profiles
        updated.append(cam["_id"])

    return {
        "status": "ok",
        "updated_camera_ids": updated,
        "mode": mode,
        "target_profile_ids": target_profile_ids,
    }
