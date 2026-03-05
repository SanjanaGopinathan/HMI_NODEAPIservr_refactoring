# mcp_server/tools/query.py
"""
Query tools for retrieving information from the surveillance system.
These tools provide read-only access to system state and configuration.
"""
from typing import Dict, Any, Optional, List
from mcp_server.server import mcp
from mcp_server.api_client import api_client


@mcp.tool()
async def query_camera_details(
    camera_id: str,
    tenant_id: str,
    site_id: str,
    gateway_id: str,
) -> Dict[str, Any]:
    """
    Get detailed information about a specific camera including all bindings.
    
    This tool fetches complete camera information and enriches it with
    related resources (model, profiles, policy details).
    
    Args:
        camera_id: Unique camera identifier
        tenant_id: Tenant identifier
        site_id: Site identifier
        gateway_id: Gateway identifier
        
    Returns:
        Complete camera object with resolved references:
        - camera: Full camera details
        - model: Assigned model details (if any)
        - profiles: List of assigned profile details
        - policy: Assigned policy details (if any)
        - status: Query status
    """
    try:
        # Fetch camera details
        camera = await api_client.get(f"/assets/{camera_id}")
        
        # Validate tenant/site/gateway
        if (camera.get("tenant_id") != tenant_id or 
            camera.get("site_id") != site_id or 
            camera.get("gateway_id") != gateway_id):
            return {
                "status": "error",
                "error": f"Camera {camera_id} not found in tenant {tenant_id}, site {site_id}, gateway {gateway_id}",
                "camera": None,
                "model": None,
                "profiles": [],
                "policy": None
            }
        
        # Extract bindings
        bindings = camera.get("asset_info", {}).get("bindings", {})
        model_id = bindings.get("assigned_model_id")
        profile_ids = bindings.get("target_profile_ids", [])
        policy_id = bindings.get("assigned_policy_id")
        
        # Fetch related resources
        model = None
        if model_id:
            try:
                model = await api_client.get(f"/models/{model_id}")
            except Exception:
                model = {"id": model_id, "error": "Model not found"}
        
        profiles = []
        for profile_id in profile_ids:
            try:
                profile = await api_client.get(f"/profiles/{profile_id}")
                profiles.append(profile)
            except Exception:
                profiles.append({"id": profile_id, "error": "Profile not found"})
        
        policy = None
        if policy_id:
            try:
                policy = await api_client.get(f"/policies/{policy_id}")
            except Exception:
                policy = {"id": policy_id, "error": "Policy not found"}
        
        return {
            "status": "success",
            "camera": camera,
            "model": model,
            "profiles": profiles,
            "policy": policy
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "camera": None,
            "model": None,
            "profiles": [],
            "policy": None
        }


@mcp.tool()
async def query_site_overview(
    tenant_id: str,
    site_id: str,
    gateway_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get overview of all resources at a site.
    
    Provides summary counts and lists of cameras, models, profiles, 
    policies, and personnel for a specific site.
    
    Args:
        tenant_id: Tenant identifier
        site_id: Site identifier
        gateway_id: Optional gateway filter
        
    Returns:
        Summary with counts and lists:
        - counts: Resource counts by type
        - cameras: List of cameras
        - models: List of models
        - profiles: List of profiles
        - policies: List of policies
        - personnel: List of personnel
    """
    try:
        # Build query parameters
        params = {
            "tenant_id": tenant_id,
            "site_id": site_id,
        }
        if gateway_id:
            params["gateway_id"] = gateway_id
        
        # Fetch all resource types
        cameras_response = await api_client.get("/assets", params={**params, "asset_type": "CAMERA"})
        models_response = await api_client.get("/models", params=params)
        profiles_response = await api_client.get("/profiles", params=params)
        policies_response = await api_client.get("/policies", params=params)
        personnel_response = await api_client.get("/personnel", params=params)
        
        # Extract items and totals
        cameras = cameras_response.get("items", [])
        models = models_response.get("items", [])
        profiles = profiles_response.get("items", [])
        policies = policies_response.get("items", [])
        personnel = personnel_response.get("items", [])
        
        # Calculate counts by status
        cameras_active = sum(1 for c in cameras if c.get("status") == "ACTIVE")
        cameras_inactive = sum(1 for c in cameras if c.get("status") == "INACTIVE")
        
        return {
            "status": "success",
            "tenant_id": tenant_id,
            "site_id": site_id,
            "gateway_id": gateway_id,
            "counts": {
                "cameras_total": len(cameras),
                "cameras_active": cameras_active,
                "cameras_inactive": cameras_inactive,
                "models": len(models),
                "profiles": len(profiles),
                "policies": len(policies),
                "personnel": len(personnel)
            },
            "cameras": cameras,
            "models": models,
            "profiles": profiles,
            "policies": policies,
            "personnel": personnel
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "counts": {},
            "cameras": [],
            "models": [],
            "profiles": [],
            "policies": [],
            "personnel": []
        }


@mcp.tool()
async def query_cameras_by_status(
    tenant_id: str,
    site_id: str,
    status: str,
    gateway_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Find all cameras with a specific status.
    
    Args:
        tenant_id: Tenant identifier
        site_id: Site identifier
        status: Camera status (ACTIVE or INACTIVE)
        gateway_id: Optional gateway filter
        
    Returns:
        List of cameras matching the status:
        - cameras: List of camera objects
        - count: Number of cameras found
    """
    try:
        params = {
            "tenant_id": tenant_id,
            "site_id": site_id,
            "status": status.upper(),
            "asset_type": "CAMERA",
            "limit": 200
        }
        if gateway_id:
            params["gateway_id"] = gateway_id
        
        response = await api_client.get("/assets", params=params)
        cameras = response.get("items", [])
        
        return {
            "status": "success",
            "cameras": cameras,
            "count": len(cameras),
            "filter": {
                "tenant_id": tenant_id,
                "site_id": site_id,
                "gateway_id": gateway_id,
                "status": status
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "cameras": [],
            "count": 0
        }


@mcp.tool()
async def query_cameras_by_location(
    tenant_id: str,
    site_id: str,
    location: str,
    gateway_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Find all cameras at a specific location.
    
    Args:
        tenant_id: Tenant identifier
        site_id: Site identifier
        location: Location name (e.g., "Gate 3", "Entry Gate")
        gateway_id: Optional gateway filter
        
    Returns:
        List of cameras at the location:
        - cameras: List of camera objects with configurations
        - count: Number of cameras found
    """
    try:
        # First get all cameras for the site
        params = {
            "tenant_id": tenant_id,
            "site_id": site_id,
            "asset_type": "CAMERA",
            "limit": 200
        }
        if gateway_id:
            params["gateway_id"] = gateway_id
        
        response = await api_client.get("/assets", params=params)
        all_cameras = response.get("items", [])
        
        # Filter by location (case-insensitive partial match)
        location_lower = location.lower()
        cameras = [
            c for c in all_cameras 
            if location_lower in c.get("location", "").lower()
        ]
        
        return {
            "status": "success",
            "cameras": cameras,
            "count": len(cameras),
            "filter": {
                "tenant_id": tenant_id,
                "site_id": site_id,
                "gateway_id": gateway_id,
                "location": location
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "cameras": [],
            "count": 0
        }


@mcp.tool()
async def query_policy_assignments(
    tenant_id: str,
    site_id: str,
    policy_id: str,
    gateway_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Find all cameras assigned to a specific policy.
    
    Args:
        tenant_id: Tenant identifier
        site_id: Site identifier
        policy_id: Policy identifier to search for
        gateway_id: Optional gateway filter
        
    Returns:
        List of cameras with the policy assigned:
        - cameras: List of camera objects
        - count: Number of cameras found
        - policy: Policy details
    """
    try:
        # Fetch policy details
        try:
            policy = await api_client.get(f"/policies/{policy_id}")
        except Exception:
            return {
                "status": "error",
                "error": f"Policy {policy_id} not found",
                "cameras": [],
                "count": 0,
                "policy": None
            }
        
        # Get all cameras for the site
        params = {
            "tenant_id": tenant_id,
            "site_id": site_id,
            "asset_type": "CAMERA",
            "limit": 200
        }
        if gateway_id:
            params["gateway_id"] = gateway_id
        
        response = await api_client.get("/assets", params=params)
        all_cameras = response.get("items", [])
        
        # Filter cameras with this policy assigned
        cameras = [
            c for c in all_cameras
            if c.get("asset_info", {}).get("bindings", {}).get("assigned_policy_id") == policy_id
        ]
        
        return {
            "status": "success",
            "cameras": cameras,
            "count": len(cameras),
            "policy": policy,
            "filter": {
                "tenant_id": tenant_id,
                "site_id": site_id,
                "gateway_id": gateway_id,
                "policy_id": policy_id
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "cameras": [],
            "count": 0,
            "policy": None
        }


@mcp.tool()
async def query_model_assignments(
    tenant_id: str,
    site_id: str,
    model_id: str,
    gateway_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Find all cameras using a specific AI model.
    
    Args:
        tenant_id: Tenant identifier
        site_id: Site identifier
        model_id: Model identifier to search for
        gateway_id: Optional gateway filter
        
    Returns:
        List of cameras with the model assigned:
        - cameras: List of camera objects
        - count: Number of cameras found
        - model: Model details
    """
    try:
        # Fetch model details
        try:
            model = await api_client.get(f"/models/{model_id}")
        except Exception:
            return {
                "status": "error",
                "error": f"Model {model_id} not found",
                "cameras": [],
                "count": 0,
                "model": None
            }
        
        # Get all cameras for the site
        params = {
            "tenant_id": tenant_id,
            "site_id": site_id,
            "asset_type": "CAMERA",
            "limit": 200
        }
        if gateway_id:
            params["gateway_id"] = gateway_id
        
        response = await api_client.get("/assets", params=params)
        all_cameras = response.get("items", [])
        
        # Filter cameras with this model assigned
        cameras = [
            c for c in all_cameras
            if c.get("asset_info", {}).get("bindings", {}).get("assigned_model_id") == model_id
        ]
        
        return {
            "status": "success",
            "cameras": cameras,
            "count": len(cameras),
            "model": model,
            "filter": {
                "tenant_id": tenant_id,
                "site_id": site_id,
                "gateway_id": gateway_id,
                "model_id": model_id
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "cameras": [],
            "count": 0,
            "model": None
        }


@mcp.tool()
async def query_profile_assignments(
    tenant_id: str,
    site_id: str,
    profile_id: str,
    gateway_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Find all cameras using specific detection profiles.
    
    Args:
        tenant_id: Tenant identifier
        site_id: Site identifier
        profile_id: Profile identifier to search for
        gateway_id: Optional gateway filter
        
    Returns:
        List of cameras with the profile in their target list:
        - cameras: List of camera objects
        - count: Number of cameras found
        - profile: Profile details
    """
    try:
        # Fetch profile details
        try:
            profile = await api_client.get(f"/profiles/{profile_id}")
        except Exception:
            return {
                "status": "error",
                "error": f"Profile {profile_id} not found",
                "cameras": [],
                "count": 0,
                "profile": None
            }
        
        # Get all cameras for the site
        params = {
            "tenant_id": tenant_id,
            "site_id": site_id,
            "asset_type": "CAMERA",
            "limit": 200
        }
        if gateway_id:
            params["gateway_id"] = gateway_id
        
        response = await api_client.get("/assets", params=params)
        all_cameras = response.get("items", [])
        
        # Filter cameras with this profile in their target list
        cameras = [
            c for c in all_cameras
            if profile_id in c.get("asset_info", {}).get("bindings", {}).get("target_profile_ids", [])
        ]
        
        return {
            "status": "success",
            "cameras": cameras,
            "count": len(cameras),
            "profile": profile,
            "filter": {
                "tenant_id": tenant_id,
                "site_id": site_id,
                "gateway_id": gateway_id,
                "profile_id": profile_id
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "cameras": [],
            "count": 0,
            "profile": None
        }


@mcp.tool()
async def query_personnel_by_role(
    tenant_id: str,
    site_id: str,
    role: str,
) -> Dict[str, Any]:
    """
    Find all personnel with a specific role.
    
    Args:
        tenant_id: Tenant identifier
        site_id: Site identifier
        role: Role name (e.g., "supervisor", "worker", "manager")
        
    Returns:
        List of personnel records:
        - personnel: List of personnel objects
        - count: Number of personnel found
    """
    try:
        params = {
            "tenant_id": tenant_id,
            "site_id": site_id,
            "role": role,
            "limit": 200
        }
        
        response = await api_client.get("/personnel", params=params)
        personnel = response.get("items", [])
        
        return {
            "status": "success",
            "personnel": personnel,
            "count": len(personnel),
            "filter": {
                "tenant_id": tenant_id,
                "site_id": site_id,
                "role": role
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "personnel": [],
            "count": 0
        }


@mcp.tool()
async def query_on_call_personnel(
    tenant_id: str,
    site_id: str,
) -> Dict[str, Any]:
    """
    Find all on-call personnel.
    
    Args:
        tenant_id: Tenant identifier
        site_id: Site identifier
        
    Returns:
        List of on-call personnel with contact info:
        - personnel: List of on-call personnel objects
        - count: Number of on-call personnel found
    """
    try:
        params = {
            "tenant_id": tenant_id,
            "site_id": site_id,
            "on_call": True,
            "limit": 200
        }
        
        response = await api_client.get("/personnel", params=params)
        personnel = response.get("items", [])
        
        return {
            "status": "success",
            "personnel": personnel,
            "count": len(personnel),
            "filter": {
                "tenant_id": tenant_id,
                "site_id": site_id,
                "on_call": True
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "personnel": [],
            "count": 0
        }


@mcp.tool()
async def query_gateways(
    tenant_id: str,
    site_id: str,
) -> Dict[str, Any]:
    """
    List all gateways for a site.
    
    Args:
        tenant_id: Tenant identifier
        site_id: Site identifier
        
    Returns:
        List of gateway objects:
        - gateways: List of gateway details
        - count: Total number of gateways
    """
    try:
        params = {
            "tenant_id": tenant_id,
            "site_id": site_id,
            "limit": 100
        }
        
        # Try /gateways endpoint first, as implied by seed data structure
        try:
            response = await api_client.get("/gateway", params=params)
            gateways = response.get("items", [])
        except Exception:
            # Fallback to assets if /gateways fails (though seed implies separate)
            params["asset_type"] = "GATEWAY"
            response = await api_client.get("/assets", params=params)
            gateways = response.get("items", [])

        return {
            "status": "success",
            "gateways": gateways,
            "count": len(gateways),
            "filter": {
                "tenant_id": tenant_id,
                "site_id": site_id
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "gateways": [],
            "count": 0
        }
