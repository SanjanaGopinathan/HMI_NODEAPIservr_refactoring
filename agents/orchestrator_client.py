# orchestrator_client.py

"""
Thin client for calling the AI Orchestrator workflows.
Used by the OpenAI tool handler.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx

ORCHESTRATOR_BASE_URL = os.getenv(
    "ORCHESTRATOR_BASE_URL",
    "http://localhost:8000",
)


def configure_ppe_workflow(
    camera_id: Optional[str] = None,
    location_filter: Optional[str] = None,
    tenant_id: Optional[str] = None,
    site_id: Optional[str] = None,
    gateway_id: Optional[str] = None,
    timeout: float = 120.0,
) -> Dict[str, Any]:
    """
    Calls the FastAPI orchestrator endpoint /workflows/configure_ppe.
    
    At least one of camera_id or location_filter must be provided.
    IDs are optional - orchestrator will use sticky defaults if not provided.

    Returns the JSON response (final PPEConfigState) as a Python dict.
    Raises httpx.HTTPStatusError if the call fails.
    """
    url = f"{ORCHESTRATOR_BASE_URL}/workflows/configure_ppe"

    payload = {}
    
    # Only include parameters if explicitly provided
    if camera_id is not None:
        payload["camera_id"] = camera_id
    if location_filter is not None:
        payload["location_filter"] = location_filter
    if tenant_id is not None:
        payload["tenant_id"] = tenant_id
    if site_id is not None:
        payload["site_id"] = site_id
    if gateway_id is not None:
        payload["gateway_id"] = gateway_id

    print(f"? Configuring PPE monitoring...")
    print(f"   This may take up to 2 minutes...")
    
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        result = resp.json()
        
    print(f"? PPE configuration completed!")
    return result
    
def route_anomaly_alert_workflow(
    tenant_id: str,
    site_id: str,
    camera_ids: List[str],
    anomaly_type: str,
    severity: str = "WARNING",
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """
    Calls the FastAPI orchestrator endpoint /workflows/route_anomaly_alert.

    Returns the JSON response (AnomalyRouteState) as a Python dict.
    Raises httpx.HTTPStatusError if the call fails.
    """
    url = f"{ORCHESTRATOR_BASE_URL}/workflows/route_anomaly_alert"

    payload = {
        "tenant_id": tenant_id,
        "site_id": site_id,
        "camera_ids": camera_ids,
        "anomaly_type": anomaly_type,
        "severity": severity,
    }

    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()


def create_camera_workflow(
    camera_id: str,
    name: str,
    rtsp_url: str,
    onvif_url: str,
    tenant_id: Optional[str] = None,
    site_id: Optional[str] = None,
    gateway_id: Optional[str] = None,
    location: Optional[str] = None,
    zone: Optional[str] = None,
    resolution: Optional[str] = None,
    fps: Optional[int] = None,
    userid: Optional[str] = None,
    password: Optional[str] = None,
    target_profile_ids: Optional[List[str]] = None,
    assigned_policy_id: Optional[str] = None,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """Create a new camera asset. IDs are optional - uses sticky defaults if not provided."""
    url = f"{ORCHESTRATOR_BASE_URL}/workflows/create_camera"

    payload = {
        "camera_id": camera_id,
        "name": name,
        "rtsp_url": rtsp_url,
        "onvif_url": onvif_url,
    }
    
    # Only include optional fields if provided
    if tenant_id is not None:
        payload["tenant_id"] = tenant_id
    if site_id is not None:
        payload["site_id"] = site_id
    if gateway_id is not None:
        payload["gateway_id"] = gateway_id
    if location is not None:
        payload["location"] = location
    if zone is not None:
        payload["zone"] = zone
    if resolution is not None:
        payload["resolution"] = resolution
    if fps is not None:
        payload["fps"] = fps
    if userid is not None:
        payload["userid"] = userid
    if password is not None:
        payload["password"] = password
    if target_profile_ids is not None:
        payload["target_profile_ids"] = target_profile_ids
    if assigned_policy_id is not None:
        payload["assigned_policy_id"] = assigned_policy_id

    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()


def delete_camera_workflow(
    camera_id: str,
    tenant_id: Optional[str] = None,
    site_id: Optional[str] = None,
    gateway_id: Optional[str] = None,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """Delete a camera asset. IDs are optional - uses sticky defaults if not provided."""
    url = f"{ORCHESTRATOR_BASE_URL}/workflows/delete_camera"

    payload = {"camera_id": camera_id}
    
    # Only include IDs if provided
    if tenant_id is not None:
        payload["tenant_id"] = tenant_id
    if site_id is not None:
        payload["site_id"] = site_id
    if gateway_id is not None:
        payload["gateway_id"] = gateway_id

    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()



def create_profile_workflow(
    profile_id: str,
    name: str,
    targets: List[str],
    tenant_id: Optional[str] = None,
    site_id: Optional[str] = None,
    gateway_id: Optional[str] = None,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """Create a new detection profile. IDs are optional - uses sticky defaults if not provided."""
    url = f"{ORCHESTRATOR_BASE_URL}/workflows/create_profile"

    payload = {
        "profile_id": profile_id,
        "name": name,
        "targets": targets,
    }
    
    # Only include IDs if provided
    if tenant_id is not None:
        payload["tenant_id"] = tenant_id
    if site_id is not None:
        payload["site_id"] = site_id
    if gateway_id is not None:
        payload["gateway_id"] = gateway_id

    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()


def create_policy_workflow(
    policy_id: str,
    anomaly_type: str,
    severity_levels: List[str],
    channels: List[str],
    person_ids: List[str],
    tenant_id: Optional[str] = None,
    site_id: Optional[str] = None,
    min_severity: Optional[str] = None,
    enabled: Optional[bool] = None,
    priority: Optional[int] = None,
    gateway_id: Optional[str] = None,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """Create a new alert policy. IDs are optional - uses sticky defaults if not provided."""
    url = f"{ORCHESTRATOR_BASE_URL}/workflows/create_policy"

    payload = {
        "policy_id": policy_id,
        "anomaly_type": anomaly_type,
        "severity_levels": severity_levels,
        "channels": channels,
        "person_ids": person_ids,
    }
    
    # Only include optional fields if provided
    if tenant_id is not None:
        payload["tenant_id"] = tenant_id
    if site_id is not None:
        payload["site_id"] = site_id
    if min_severity is not None:
        payload["min_severity"] = min_severity
    if enabled is not None:
        payload["enabled"] = enabled
    if priority is not None:
        payload["priority"] = priority

    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()


def create_personnel_workflow(
    person_id: str,
    name: str,
    role: str,
    tenant_id: Optional[str] = None,
    site_id: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    sip_uri: Optional[str] = None,
    on_call: bool = False,
    status: str = "ACTIVE",
    gateway_id: Optional[str] = None,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """Create a new personnel record. IDs are optional - uses sticky defaults if not provided."""
    url = f"{ORCHESTRATOR_BASE_URL}/workflows/create_personnel"

    payload = {
        "person_id": person_id,
        "name": name,
        "role": role,
        "on_call": on_call,
        "status": status,
    }
    
    # Only include optional fields if provided
    if tenant_id is not None:
        payload["tenant_id"] = tenant_id
    if site_id is not None:
        payload["site_id"] = site_id
    if phone is not None:
        payload["phone"] = phone
    if email is not None:
        payload["email"] = email
    if sip_uri is not None:
        payload["sip_uri"] = sip_uri

    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()


def setup_ppe_site_workflow(
    tenant_id: str,
    site_id: str,
    gateway_id: str,
    cameras_config: List[Dict[str, Any]],
    personnel_ids: Optional[List[str]] = None,
    timeout: float = 60.0,  # Longer timeout for complete setup
) -> Dict[str, Any]:
    """Complete PPE site setup - creates cameras, profiles, policies, and configures everything"""
    url = f"{ORCHESTRATOR_BASE_URL}/workflows/setup_ppe_site"

    payload = {
        "tenant_id": tenant_id,
        "site_id": site_id,
        "gateway_id": gateway_id,
        "cameras_config": cameras_config,
        "personnel_ids": personnel_ids,
    }

    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()


def disable_ppe(
    camera_id: str,
    tenant_id: Optional[str] = None,
    site_id: Optional[str] = None,
    gateway_id: Optional[str] = None,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """
    Disable PPE monitoring for a camera by calling the MCP tool directly.
    
    This is a direct MCP tool call, not an orchestrator workflow.
    It sets camera status to INACTIVE and cleans up legacy sensor data.
    
    IDs are optional - uses sticky defaults if not provided.
    """
    # Import MCP client here to avoid circular imports
    import sys
    import os
    
    # Add parent directory to path to import from orchestrator
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    from orchestrator.mcp_client import MCPClient
    from orchestrator.config import get_current_tenant_id, get_current_site_id, get_current_gateway_id
    
    # Apply defaults if not provided
    final_tenant = tenant_id or get_current_tenant_id(use_last_used=True)
    final_site = site_id or get_current_site_id(use_last_used=True)
    final_gateway = gateway_id or get_current_gateway_id(use_last_used=True)
    
    # Create MCP client and call the tool
    import asyncio
    
    async def _call_disable_ppe():
        mcp = MCPClient()
        result = await mcp.call_tool(
            "disable_ppe",
            {
                "camera_id": camera_id,
                "tenant_id": final_tenant,
                "site_id": final_site,
                "gateway_id": final_gateway
            }
        )
        return result
    
    # Run the async function
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_call_disable_ppe())


# --- Query Functions ---

def query_camera_full_context(
    camera_id: str,
    tenant_id: Optional[str] = None,
    site_id: Optional[str] = None,
    gateway_id: Optional[str] = None,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """
    Get complete context for a camera including all related resources.
    
    Returns camera details along with assigned model, profiles, policy, and personnel.
    IDs are optional - uses sticky defaults if not provided.
    """
    url = f"{ORCHESTRATOR_BASE_URL}/query/camera-full-context"
    
    payload = {"camera_id": camera_id}
    
    if tenant_id is not None:
        payload["tenant_id"] = tenant_id
    if site_id is not None:
        payload["site_id"] = site_id
    if gateway_id is not None:
        payload["gateway_id"] = gateway_id
    
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()


def query_site_health(
    tenant_id: Optional[str] = None,
    site_id: Optional[str] = None,
    gateway_id: Optional[str] = None,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """
    Analyze site health and get recommendations.
    
    Returns health score, camera status counts, unconfigured cameras,
    and recommendations for improving site configuration.
    IDs are optional - uses sticky defaults if not provided.
    """
    url = f"{ORCHESTRATOR_BASE_URL}/query/site-health"
    
    payload = {}
    
    if tenant_id is not None:
        payload["tenant_id"] = tenant_id
    if site_id is not None:
        payload["site_id"] = site_id
    if gateway_id is not None:
        payload["gateway_id"] = gateway_id
    
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()


def query_ppe_configuration_status(
    tenant_id: Optional[str] = None,
    site_id: Optional[str] = None,
    gateway_id: Optional[str] = None,
    location_filter: Optional[str] = None,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """
    Check PPE configuration status for cameras.
    
    Categorizes cameras by configuration completeness:
    - Fully configured: Has PPE model + profile + policy
    - Partially configured: Has some components
    - Not configured: No PPE components
    
    IDs are optional - uses sticky defaults if not provided.
    """
    url = f"{ORCHESTRATOR_BASE_URL}/query/ppe-status"
    
    payload = {}
    
    if tenant_id is not None:
        payload["tenant_id"] = tenant_id
    if site_id is not None:
        payload["site_id"] = site_id
    if gateway_id is not None:
        payload["gateway_id"] = gateway_id
    if location_filter is not None:
        payload["location_filter"] = location_filter
    
    with httpx.Client(timeout=timeout) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()


def query_sticky_defaults(
    timeout: float = 10.0,
) -> Dict[str, Any]:
    """
    Get current sticky default values.
    
    Returns the current tenant_id, site_id, and gateway_id that will be used
    when not explicitly provided in requests.
    """
    url = f"{ORCHESTRATOR_BASE_URL}/query/sticky-defaults"
    
    with httpx.Client(timeout=timeout) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.json()
