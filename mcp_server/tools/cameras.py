# mcp_server/tools/cameras.py
#from fastmcp import tool
from typing import Dict, Any, Optional
from mcp_server.data_store import MOCK_CAMERAS
from mcp_server.server import mcp

import os
import httpx

APP_BASE_URL = os.getenv(
    "APP_COMPONENT_BASE_URL",
    "http://localhost:6000",
)


@mcp.tool()
async def list_cameras(
    tenant_id: str,
    site_id: Optional[str] = None,
    location: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    include_counts: bool = True,
) -> Dict[str, Any]:
    """
    List cameras for a tenant/site/location from canned in-memory data.
    """
    payload = {
        "tenant_id": tenant_id,
        "site_id": site_id,
        "location": location,
        "status": status,
    }

    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.post(
            f"{APP_BASE_URL}/api/camera/list",
            json=payload,
        )

    if resp.status_code != 200:
        raise RuntimeError(
            f"AppComponent error {resp.status_code}: {resp.text}"
        )

    data = resp.json()
    print("Data received from the Node", data)
    cameras = data["cameras"]
    
    

    cams = [
        cam for cam in cameras
        if cam["tenant_id"] == tenant_id
    ]
    # cams = [
    #     cam for cam in MOCK_CAMERAS
    #     if cam["tenant_id"] == tenant_id
    # ]


    if site_id is not None:
        cams = [c for c in cams if c["site_id"] == site_id]

    if location is not None:
        # simple case-insensitive containment filter
        loc_lower = location.lower()
        cams = [c for c in cams if loc_lower in c.get("location", "").lower()]

    if status is not None:
        cams = [c for c in cams if c.get("status") == status]

    total = len(cams)
    cams = cams[offset: offset + limit]

    return {
        "cameras": cams,
        "total": total if include_counts else None,
    }
