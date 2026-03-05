from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from orchestrator.config import (
    get_current_tenant_id, 
    get_current_site_id, 
    get_current_gateway_id,
    update_defaults,
    update_last_used,
    get_all_defaults,
    get_last_used,
    get_effective_defaults,
    clear_last_used,
    reset_defaults
)

from orchestrator.mcp_client import MCPClient
from orchestrator.workflows.configure_ppe import run_configure_ppe_workflow
from orchestrator.workflows.route_anomaly_alert import run_route_anomaly_alert_workflow
from orchestrator.workflows.create_camera import run_create_camera_workflow
from orchestrator.workflows.delete_camera import run_delete_camera_workflow
from orchestrator.workflows.create_profile import run_create_profile_workflow
from orchestrator.workflows.create_policy import run_create_policy_workflow
from orchestrator.workflows.create_personnel import run_create_personnel_workflow
from orchestrator.workflows.create_model import run_create_model_workflow
from orchestrator.workflows.update_profile import run_update_profile_workflow
from orchestrator.workflows.setup_ppe_site import run_setup_ppe_site_workflow
from orchestrator.workflows.update_policy import run_update_policy_workflow
from orchestrator.workflows.query_workflows import (
    run_camera_full_context_query,
    run_site_health_query,
    run_ppe_config_status_query
)
from orchestrator.api.stream import router as stream_router

app = FastAPI(title="AI Orchestrator – Enable PPE Monitoring")

# Configure CORS
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stream_router)

mcp_client = MCPClient()


# --- Request Schemas ---

class ConfigurePPERequest(BaseModel):
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    gateway_id: Optional[str] = None
    camera_id: Optional[str] = None
    location_filter: Optional[str] = None

class AnomalyRequest(BaseModel):
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    camera_ids: List[str]
    anomaly_type: str
    severity: str

class CreateCameraRequest(BaseModel):
    camera_id: str
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    gateway_id: Optional[str] = None
    name: str
    rtsp_url: str
    onvif_url: str
    location: Optional[str] = None
    zone: Optional[str] = None
    resolution: Optional[str] = None
    fps: Optional[int] = None
    userid: Optional[str] = None
    password: Optional[str] = None
    target_profile_ids: Optional[List[str]] = None
    assigned_policy_id: Optional[str] = None


class DeleteCameraRequest(BaseModel):
    camera_id: str
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    gateway_id: Optional[str] = None

class CreateProfileRequest(BaseModel):
    profile_id: str
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    gateway_id: Optional[str] = None
    name: str
    targets: List[str]

class UpdateProfileRequest(BaseModel):
    profile_id: str
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    gateway_id: Optional[str] = None
    name: Optional[str] = None
    targets: Optional[List[str]] = None

class CreateModelRequest(BaseModel):
    model_id: str
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    gateway_id: Optional[str] = None
    name: str
    framework_id: str
    supported_profile_ids: Optional[List[str]] = None
    status: Optional[str] = "ACTIVE"

class AssignCamerasToModelRequest(BaseModel):
    model_id: str
    camera_ids: List[str]
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    gateway_id: Optional[str] = None
    auto_adjust_stream_profile: Optional[bool] = True

class CreatePolicyRequest(BaseModel):
    policy_id: str
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    anomaly_type: str
    severity_levels: List[str]
    channels: List[str]
    person_ids: List[str]
    min_severity: Optional[str] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None

class UpdatePolicyRequest(BaseModel):
    policy_id: str
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    anomaly_type: Optional[str] = None
    severity_levels: Optional[List[str]] = None
    channels: Optional[List[str]] = None
    person_ids: Optional[List[str]] = None
    min_severity: Optional[str] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None

class CreatePersonnelRequest(BaseModel):
    person_id: str
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    name: str
    role: str
    phone: Optional[str] = None
    email: Optional[str] = None
    sip_uri: Optional[str] = None
    on_call: bool = False
    status: str = "ACTIVE"

class SetupPPESiteRequest(BaseModel):
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    gateway_id: Optional[str] = None
    cameras_config: List[Dict[str, Any]]
    personnel_ids: Optional[List[str]] = None


# Helper function to apply runtime defaults with sticky behavior
def apply_defaults(
    tenant_id: Optional[str], 
    site_id: Optional[str], 
    gateway_id: Optional[str],
    use_sticky: bool = True
) -> tuple:
    """
    Apply runtime defaults to None values.
    
    Args:
        tenant_id: Provided tenant ID (or None)
        site_id: Provided site ID (or None)
        gateway_id: Provided gateway ID (or None)
        use_sticky: If True, use sticky behavior (remember last-used values)
    
    Returns:
        Tuple of (tenant_id, site_id, gateway_id) with defaults applied
    """
    # Track which values were explicitly provided
    provided_tenant = tenant_id is not None
    provided_site = site_id is not None
    provided_gateway = gateway_id is not None
    
    # Apply defaults (with sticky behavior if enabled)
    final_tenant = tenant_id or get_current_tenant_id(use_last_used=use_sticky)
    final_site = site_id or get_current_site_id(use_last_used=use_sticky)
    final_gateway = gateway_id or get_current_gateway_id(use_last_used=use_sticky)
    
    # Update last-used values for explicitly provided IDs (all in one call)
    if use_sticky and (provided_tenant or provided_site or provided_gateway):
        update_last_used(
            tenant_id=final_tenant if provided_tenant else None,
            site_id=final_site if provided_site else None,
            gateway_id=final_gateway if provided_gateway else None
        )
        # Debug logging
        print(f"[STICKY] Updated last-used: tenant={final_tenant if provided_tenant else 'unchanged'}, "
              f"site={final_site if provided_site else 'unchanged'}, "
              f"gateway={final_gateway if provided_gateway else 'unchanged'}")
    
    return (final_tenant, final_site, final_gateway)



# --- Endpoints ---

@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "component": "orchestrator"}


@app.post("/workflows/configure_ppe", tags=["workflows"])
async def configure_ppe(req: ConfigurePPERequest):
    """
    Entry point for the 'Enable PPE monitoring' use case.
    Typically called by LLM agents or UI.
    """
    print(f"[REQUEST] Received: tenant={req.tenant_id}, site={req.site_id}, gateway={req.gateway_id}, camera_id={req.camera_id}, location={req.location_filter}")
    tenant_id, site_id, gateway_id = apply_defaults(req.tenant_id, req.site_id, req.gateway_id)
    print(f"[RESOLVED] Using: tenant={tenant_id}, site={site_id}, gateway={gateway_id}")
    
    # Validate: at least one filter must be provided
    if not req.camera_id and not req.location_filter:
        return {
            "error": "At least one of camera_id or location_filter must be provided",
            "status": "error"
        }
    
    state = await run_configure_ppe_workflow(
        mcp=mcp_client,
        tenant_id=tenant_id,
        site_id=site_id,
        gateway_id=gateway_id,
        camera_id=req.camera_id,
        location_filter=req.location_filter,
        status="INACTIVE"
    )
    return state


class DisablePPERequest(BaseModel):
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    gateway_id: Optional[str] = None
    camera_id: str

@app.post("/workflows/disable_ppe", tags=["workflows"])
async def disable_ppe(req: DisablePPERequest):
    """
    Disable PPE monitoring for a specific camera.
    Uses the 'disable_ppe' tool.
    """
    tenant_id, site_id, gateway_id = apply_defaults(req.tenant_id, req.site_id, req.gateway_id)
    
    try:
        # Call the tool directly as we don't have a specific wrapper workflow yet
        # or we could assume mcp_client has call_tool
        result = await mcp_client.call_tool(
            "disable_ppe", 
            {
                "camera_id": req.camera_id,
                "tenant_id": tenant_id,
                "site_id": site_id,
                "gateway_id": gateway_id
            }
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/workflows/route_anomaly_alert", tags=["workflows"])
async def route_anomaly_alert(req: AnomalyRequest):
    """
    Entry point for the 'Routing anomaly alerts' use case.
    Typically called by LLM agents or UI.
    """
    tenant_id, site_id, _ = apply_defaults(req.tenant_id, req.site_id, None)
    
    state = await run_route_anomaly_alert_workflow(
        mcp=mcp_client,
        tenant_id=tenant_id,
        site_id=site_id,
        camera_ids=req.camera_ids or ["Gate 3"],
        anomaly_type=req.anomaly_type,
        severity=req.severity or "WARNING"
    )
    return state

@app.post("/workflows/create_camera", tags=["workflows", "creation"])
async def create_camera(req: CreateCameraRequest):
    """Create a new camera asset"""
    # Apply runtime defaults
    data = req.dict()
    data['tenant_id'], data['site_id'], data['gateway_id'] = apply_defaults(
        data.get('tenant_id'), data.get('site_id'), data.get('gateway_id')
    )
    
    state = await run_create_camera_workflow(
        mcp=mcp_client,
        **data
    )
    return state

@app.post("/workflows/delete_camera", tags=["workflows", "deletion"])
async def delete_camera(req: DeleteCameraRequest):
    """Delete a camera asset"""
    tenant_id, site_id, gateway_id = apply_defaults(req.tenant_id, req.site_id, req.gateway_id)
    
    state = await run_delete_camera_workflow(
        mcp=mcp_client,
        camera_id=req.camera_id,
        tenant_id=tenant_id,
        site_id=site_id,
        gateway_id=gateway_id
    )
    return state

@app.post("/workflows/create_profile", tags=["workflows", "creation"])
async def create_profile(req: CreateProfileRequest):
    """Create a new detection profile"""
    data = req.dict()
    data['tenant_id'], data['site_id'], data['gateway_id'] = apply_defaults(
        data.get('tenant_id'), data.get('site_id'), data.get('gateway_id')
    )
    
    state = await run_create_profile_workflow(
        mcp=mcp_client,
        **data
    )
    return state

@app.post("/workflows/update_profile", tags=["workflows", "management"])
async def update_profile(req: UpdateProfileRequest):
    """Update an existing detection profile"""
    data = req.dict(exclude_unset=True)
    
    # Extract IDs for default application
    tenant_id = data.get('tenant_id')
    site_id = data.get('site_id')
    gateway_id = data.get('gateway_id')
    
    # Apply defaults
    data['tenant_id'], data['site_id'], data['gateway_id'] = apply_defaults(
        tenant_id, site_id, gateway_id
    )
    
    state = await run_update_profile_workflow(
        mcp=mcp_client,
        **data
    )
    
    if state["status"] == "error" or state["status"] == "not_found":
         raise HTTPException(status_code=400, detail=state.get("error_reason", "Update failed"))
         
    return state["result"]

@app.post("/workflows/create_model", tags=["workflows", "creation"])
async def create_model(req: CreateModelRequest):
    """Create a new AI model"""
    data = req.dict()
    data['tenant_id'], data['site_id'], data['gateway_id'] = apply_defaults(
        data.get('tenant_id'), data.get('site_id'), data.get('gateway_id')
    )
    
    state = await run_create_model_workflow(
        mcp=mcp_client,
        **data
    )
    return state

@app.post("/workflows/assign_cameras_to_model", tags=["workflows", "management"])
async def assign_cameras_to_model(req: AssignCamerasToModelRequest):
    """Assign cameras to a model"""
    # Apply runtime defaults
    tenant_id, site_id, gateway_id = apply_defaults(req.tenant_id, req.site_id, req.gateway_id)
    
    try:
        result = await mcp_client.call_tool("assign_cameras_to_model", {
            "tenant_id": tenant_id,
            "site_id": site_id,
            "gateway_id": gateway_id,
            "model_id": req.model_id,
            "camera_ids": req.camera_ids,
            "auto_adjust_stream_profile": req.auto_adjust_stream_profile
        })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workflows/create_policy", tags=["workflows", "creation"])
async def create_policy(req: CreatePolicyRequest):
    """Create a new alert policy"""
    data = req.dict()
    data['tenant_id'], data['site_id'], _ = apply_defaults(
        data.get('tenant_id'), data.get('site_id'), None
    )
    
    state = await run_create_policy_workflow(
        mcp=mcp_client,
        **data
    )
    return state

@app.post("/workflows/update_policy", tags=["workflows", "management"])
async def update_policy(req: UpdatePolicyRequest):
    """Update an existing alert policy"""
    data = req.dict(exclude_unset=True)
    
    # Extract IDs for default application
    tenant_id = data.get('tenant_id')
    site_id = data.get('site_id')
    
    # Apply defaults
    data['tenant_id'], data['site_id'], _ = apply_defaults(
        tenant_id, site_id, None
    )
    
    state = await run_update_policy_workflow(
        mcp=mcp_client,
        **data
    )
    
    if state["status"] == "error":
         raise HTTPException(status_code=400, detail=state.get("error_reason", "Update failed"))
         
    return state["result"]

@app.post("/workflows/create_personnel", tags=["workflows", "creation"])
async def create_personnel(req: CreatePersonnelRequest):
    """Create a new personnel record"""
    data = req.dict()
    data['tenant_id'], data['site_id'], _ = apply_defaults(
        data.get('tenant_id'), data.get('site_id'), None
    )
    
    state = await run_create_personnel_workflow(
        mcp=mcp_client,
        **data
    )
    return state

@app.post("/workflows/setup_ppe_site", tags=["workflows", "creation"])
async def setup_ppe_site(req: SetupPPESiteRequest):
    """Complete PPE site setup - creates cameras, profiles, policies, and configures everything"""
    data = req.dict()
    data['tenant_id'], data['site_id'], data['gateway_id'] = apply_defaults(
        data.get('tenant_id'), data.get('site_id'), data.get('gateway_id')
    )
    
    state = await run_setup_ppe_site_workflow(
        mcp=mcp_client,
        **data
    )
    return state


# --- Query Request Schemas ---

class CameraFullContextRequest(BaseModel):
    """Request for camera full context query"""
    camera_id: str
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    gateway_id: Optional[str] = None


class SiteHealthRequest(BaseModel):
    """Request for site health query"""
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    gateway_id: Optional[str] = None


class PPEConfigStatusRequest(BaseModel):
    """Request for PPE configuration status query"""
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    gateway_id: Optional[str] = None
    location_filter: Optional[str] = None


# --- Query Endpoints ---

@app.post("/query/camera-full-context", tags=["queries"])
async def query_camera_full_context(req: CameraFullContextRequest):
    """
    Get complete context for a camera including all related resources.
    
    Returns:
        - camera: Full camera details
        - model: Assigned model details
        - profiles: All assigned detection profiles
        - policy: Assigned alert policy
        - personnel: Personnel associated with the policy
    """
    tenant_id, site_id, gateway_id = apply_defaults(req.tenant_id, req.site_id, req.gateway_id)
    
    state = await run_camera_full_context_query(
        mcp=mcp_client,
        camera_id=req.camera_id,
        tenant_id=tenant_id,
        site_id=site_id,
        gateway_id=gateway_id
    )
    return state


@app.post("/query/site-health", tags=["queries"])
async def query_site_health(req: SiteHealthRequest):
    """
    Analyze site health and provide recommendations.
    
    Returns:
        - health_score: Overall health score (0-100)
        - cameras_active/inactive: Camera status counts
        - cameras_without_model/policy/profiles: Lists of unconfigured cameras
        - recommendations: List of recommended actions
        - issues: Detailed list of issues found
    """
    tenant_id, site_id, gateway_id = apply_defaults(req.tenant_id, req.site_id, req.gateway_id)
    
    state = await run_site_health_query(
        mcp=mcp_client,
        tenant_id=tenant_id,
        site_id=site_id,
        gateway_id=gateway_id
    )
    return state


@app.post("/query/ppe-status", tags=["queries"])
async def query_ppe_configuration_status(req: PPEConfigStatusRequest):
    """
    Check PPE configuration status for cameras.
    
    Categorizes cameras by configuration completeness:
    - Fully configured: Has PPE model + profile + policy
    - Partially configured: Has some but not all components
    - Not configured: Has no PPE components
    
    Returns:
        - fully_configured: List of camera IDs
        - partially_configured: List of camera IDs
        - not_configured: List of camera IDs
        - configuration_details: Detailed config for each camera
    """
    tenant_id, site_id, gateway_id = apply_defaults(req.tenant_id, req.site_id, req.gateway_id)
    
    state = await run_ppe_config_status_query(
        mcp=mcp_client,
        tenant_id=tenant_id,
        site_id=site_id,
        gateway_id=gateway_id,
        location_filter=req.location_filter
    )
    return state


class ListCamerasRequest(BaseModel):
    """Request to list cameras with filters"""
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    gateway_id: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None


@app.post("/query/cameras", tags=["queries"])
async def list_cameras(req: ListCamerasRequest):
    """
    List cameras based on provided filters.
    Directly calls the MCP 'list_cameras' tool.
    """
    tenant_id, site_id, gateway_id = apply_defaults(req.tenant_id, req.site_id, req.gateway_id)
    
    # Construct arguments for MCP tool
    args = {
        "tenant_id": tenant_id,
        "site_id": site_id,
        "gateway_id": gateway_id
    }
    if req.location:
        args["location"] = req.location
    if req.status:
        args["status"] = req.status
    
    print(f"[DEBUG] Calling list_cameras with args: {args}")
    
    try:
        # Call MCP tool directly for simple list operations
        print(f"[DEBUG] Current time: {datetime.now().isoformat()}")
        result = await mcp_client.call_tool("list_cameras", args)
        print(f"[DEBUG] Current time: {datetime.now().isoformat()}")
        print(f"[DEBUG] MCP tool returned: {result}")
        return result
    except Exception as e:
        print(f"[DEBUG] MCP tool error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


class ListModelsRequest(BaseModel):
    """Request to list models with filters"""
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    framework_id: Optional[str] = None
    framework_id: Optional[str] = None
    status: Optional[str] = None

class ListGatewaysRequest(BaseModel):
    """Request to list gateways with filters"""
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None

@app.post("/query/gateways", tags=["queries"])
async def list_gateways(req: ListGatewaysRequest):
    """List gateways based on provided filters."""
    tenant_id, site_id, _ = apply_defaults(req.tenant_id, req.site_id, None)
    
    args = {
        "tenant_id": tenant_id,
        "site_id": site_id
    }
    
    try:
        result = await mcp_client.call_tool("query_gateways", args)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query/models", tags=["queries"])
async def list_models(req: ListModelsRequest):
    """List models based on provided filters."""
    tenant_id, site_id, _ = apply_defaults(req.tenant_id, req.site_id, None)
    
    args = {
        "tenant_id": tenant_id,
        "site_id": site_id
    }
    if req.framework_id:
        args["framework_id"] = req.framework_id
    if req.status:
        args["status"] = req.status
        
    try:
        result = await mcp_client.call_tool("list_models", args)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class UpdateCameraRequest(BaseModel):
    """Request to update camera details"""
    camera_id: str
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    gateway_id: Optional[str] = None
    name: Optional[str] = None
    location: Optional[str] = None
    zone: Optional[str] = None
    status: Optional[str] = None
    rtsp_url: Optional[str] = None
    onvif_url: Optional[str] = None
    fps: Optional[int] = None
    resolution: Optional[str] = None
    userid: Optional[str] = None
    password: Optional[str] = None
    tags: Optional[List[str]] = None
    assigned_model_id: Optional[str] = None
    target_profile_ids: Optional[List[str]] = None
    assigned_policy_id: Optional[str] = None

@app.post("/workflows/update_camera", tags=["workflows", "management"])
async def update_camera(req: UpdateCameraRequest):
    """Update camera details including bindings"""
    data = req.dict(exclude_unset=True)
    
    # Extract IDs for default application
    tenant_id = data.get('tenant_id')
    site_id = data.get('site_id')
    gateway_id = data.get('gateway_id')
    
    # Apply defaults
    data['tenant_id'], data['site_id'], data['gateway_id'] = apply_defaults(
        tenant_id, site_id, gateway_id
    )
    
    try:
        result = await mcp_client.call_tool("update_camera", data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ListProfilesRequest(BaseModel):
    """Request to list profiles with filters"""
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    target_name_contains: Optional[str] = None

@app.post("/query/profiles", tags=["queries"])
async def list_profiles(req: ListProfilesRequest):
    """List detection profiles based on provided filters."""
    tenant_id, site_id, _ = apply_defaults(req.tenant_id, req.site_id, None)
    
    args = {
        "tenant_id": tenant_id,
        "site_id": site_id
    }
    if req.target_name_contains:
        args["target_name_contains"] = req.target_name_contains
        
    try:
        result = await mcp_client.call_tool("list_profiles", args)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ListPoliciesRequest(BaseModel):
    """Request to list policies with filters"""
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    anomaly_type: Optional[str] = None
    enabled: Optional[bool] = None

@app.post("/query/policies", tags=["queries"])
async def list_policies(req: ListPoliciesRequest):
    """List policies based on provided filters."""
    tenant_id, site_id, _ = apply_defaults(req.tenant_id, req.site_id, None)
    
    args = {
        "tenant_id": tenant_id,
        "site_id": site_id
    }
    if req.anomaly_type:
        args["anomaly_type"] = req.anomaly_type
    if req.enabled is not None:
        args["enabled"] = req.enabled
        
    try:
        # Note: Tool name is 'list_policy' (singular) as verified
        result = await mcp_client.call_tool("list_policy", args)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ListPersonnelRequest(BaseModel):
    """Request to list personnel with filters"""
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    role: Optional[str] = None
    on_call: Optional[bool] = None

@app.post("/query/personnel", tags=["queries"])
async def list_personnel(req: ListPersonnelRequest):
    """List personnel based on provided filters."""
    tenant_id, site_id, _ = apply_defaults(req.tenant_id, req.site_id, None)
    
    args = {
        "tenant_id": tenant_id,
        "site_id": site_id
    }
    if req.role:
        args["role"] = req.role
    if req.on_call is not None:
        args["on_call"] = req.on_call
        
    try:
        result = await mcp_client.call_tool("list_personnel", args)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/query/sticky-defaults", tags=["queries", "configuration"])
async def query_sticky_defaults():
    """
    Get current sticky default values.
    
    Returns the current tenant_id, site_id, and gateway_id that will be used
    when not explicitly provided in requests. Includes both runtime defaults
    and last-used (sticky) values.
    """
    return {
        "effective_defaults": get_effective_defaults(use_last_used=True),
        "runtime_defaults": get_all_defaults(),
        "last_used": get_last_used()
    }


# --- Configuration Management Endpoints ---

class UpdateDefaultsRequest(BaseModel):
    """Request to update default IDs"""
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None
    gateway_id: Optional[str] = None


@app.get("/config/defaults", tags=["configuration"])
async def get_defaults():
    """
    Get current default tenant_id, site_id, and gateway_id.
    These defaults are used when not explicitly provided in workflow requests.
    """
    return get_all_defaults()


@app.put("/config/defaults", tags=["configuration"])
async def set_defaults(req: UpdateDefaultsRequest):
    """
    Update default tenant_id, site_id, and/or gateway_id at runtime.
    Only provided values will be updated; others remain unchanged.
    
    Example:
        PUT /config/defaults
        {
            "tenant_id": "TENANT_02",
            "site_id": "SITE_02"
        }
    
    This will update tenant and site, but keep the current gateway_id.
    """
    update_defaults(
        tenant_id=req.tenant_id,
        site_id=req.site_id,
        gateway_id=req.gateway_id
    )
    return {
        "status": "updated",
        "current_defaults": get_all_defaults()
    }


@app.post("/config/defaults/reset", tags=["configuration"])
async def reset_defaults_endpoint():
    """
    Reset defaults to original config file values.
    Useful if you want to revert runtime changes.
    Also clears last-used (sticky) values.
    """
    reset_defaults()
    return {
        "status": "reset",
        "current_defaults": get_all_defaults(),
        "last_used": get_last_used()
    }


@app.get("/config/defaults/effective", tags=["configuration"])
async def get_effective_defaults_endpoint(use_sticky: bool = True):
    """
    Get effective defaults that will be used for the next request.
    
    Args:
        use_sticky: If True, includes sticky (last-used) values in priority
    
    Returns effective defaults considering:
    - Last-used values (if use_sticky=True and available)
    - Runtime defaults
    """
    return {
        "effective_defaults": get_effective_defaults(use_last_used=use_sticky),
        "runtime_defaults": get_all_defaults(),
        "last_used": get_last_used(),
        "sticky_enabled": use_sticky
    }


@app.get("/config/defaults/last-used", tags=["configuration"])
async def get_last_used_endpoint():
    """
    Get the last explicitly provided values (sticky defaults).
    These are the IDs that were most recently provided in requests.
    
    Returns None for values that haven't been explicitly provided yet.
    """
    return {
        "last_used": get_last_used(),
        "note": "These values are remembered from your last explicit requests"
    }


@app.post("/config/defaults/clear-sticky", tags=["configuration"])
async def clear_sticky_defaults():
    """
    Clear last-used (sticky) values.
    After this, defaults will fall back to runtime defaults.
    """
    clear_last_used()
    return {
        "status": "cleared",
        "last_used": get_last_used(),
        "current_defaults": get_all_defaults()
    }

# --- Configuration Endpoint ---

class ConfigureMapperRequest(BaseModel):
    gateway_id: str

@app.post("/api/configure", tags=["configuration"])
async def configure_mapper(req: ConfigureMapperRequest):
    """
    Configure the HMI Mapper context (Edge AI credentials) for the session.
    Passthrough to MCP Tool -> HMI Mapper API.
    """
    print(f"[CONFIG] Switching context to gateway: {req.gateway_id}")
    
    # Also update sticky default for gateway_id
    update_defaults(gateway_id=req.gateway_id)
    update_last_used(gateway_id=req.gateway_id)
    
    try:
        result = await mcp_client.call_tool("configure_mapper", {"gateway_id": req.gateway_id})
        return result
    except Exception as e:
        print(f"❌ Error configuring mapper: {e}")
        # If MCP fails, we still updated the orchestrator defaults which is good
        raise HTTPException(status_code=500, detail=str(e))

