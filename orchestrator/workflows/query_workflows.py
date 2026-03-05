# orchestrator/workflows/query_workflows.py
"""
Advanced query workflows that orchestrate multiple MCP tool calls
to provide complex, multi-resource query capabilities.
"""
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from orchestrator.mcp_client import MCPClient


# --- State Definitions ---

class CameraFullContextState(TypedDict, total=False):
    """State for camera full context query workflow"""
    # Input
    camera_id: str
    tenant_id: str
    site_id: str
    gateway_id: str
    
    # Intermediate data
    camera: Optional[Dict[str, Any]]
    model: Optional[Dict[str, Any]]
    profiles: List[Dict[str, Any]]
    policy: Optional[Dict[str, Any]]
    personnel: List[Dict[str, Any]]
    
    # Status
    status: str
    error: Optional[str]


class SiteHealthState(TypedDict, total=False):
    """State for site health query workflow"""
    # Input
    tenant_id: str
    site_id: str
    gateway_id: Optional[str]
    
    # Intermediate data
    cameras: List[Dict[str, Any]]
    models: List[Dict[str, Any]]
    profiles: List[Dict[str, Any]]
    policies: List[Dict[str, Any]]
    
    # Analysis results
    cameras_active: int
    cameras_inactive: int
    cameras_without_model: List[str]
    cameras_without_policy: List[str]
    cameras_without_profiles: List[str]
    
    # Health report
    health_score: int  # 0-100
    recommendations: List[str]
    issues: List[Dict[str, Any]]
    
    # Status
    status: str
    error: Optional[str]


class PPEConfigStatusState(TypedDict, total=False):
    """State for PPE configuration status query workflow"""
    # Input
    tenant_id: str
    site_id: str
    gateway_id: Optional[str]
    location_filter: Optional[str]
    
    # Intermediate data
    cameras: List[Dict[str, Any]]
    ppe_profiles: List[Dict[str, Any]]
    ppe_models: List[Dict[str, Any]]
    ppe_policies: List[Dict[str, Any]]
    
    # Configuration status
    fully_configured: List[str]  # Camera IDs
    partially_configured: List[str]
    not_configured: List[str]
    configuration_details: Dict[str, Dict[str, Any]]  # camera_id -> config details
    
    # Status
    status: str
    error: Optional[str]


# --- Node Implementations ---

# Camera Full Context Workflow

async def node_fetch_camera(state: CameraFullContextState, mcp: MCPClient) -> CameraFullContextState:
    """Fetch camera details"""
    try:
        result = await mcp.call_tool(
            "query_camera_details",
            {
                "camera_id": state["camera_id"],
                "tenant_id": state["tenant_id"],
                "site_id": state["site_id"],
                "gateway_id": state["gateway_id"]
            }
        )
        
        if result.get("status") == "success":
            return {
                **state,
                "camera": result.get("camera"),
                "model": result.get("model"),
                "profiles": result.get("profiles", []),
                "policy": result.get("policy"),
                "status": "camera_fetched"
            }
        else:
            return {
                **state,
                "status": "error",
                "error": result.get("error", "Failed to fetch camera")
            }
    except Exception as e:
        return {
            **state,
            "status": "error",
            "error": str(e)
        }


async def node_fetch_personnel(state: CameraFullContextState, mcp: MCPClient) -> CameraFullContextState:
    """Fetch personnel associated with the policy"""
    if not state.get("policy"):
        return {**state, "personnel": [], "status": "complete"}
    
    try:
        # Extract person IDs from policy routes
        policy = state["policy"]
        person_ids = set()
        
        for route in policy.get("routes", []):
            for target in route.get("targets", []):
                if target.get("target_type") == "PERSON":
                    person_ids.add(target.get("value"))
        
        # Fetch personnel details
        personnel = []
        for person_id in person_ids:
            try:
                # Note: We'd need a get_personnel_by_id tool, for now use list with filter
                result = await mcp.call_tool(
                    "list_personnel",
                    {
                        "tenant_id": state["tenant_id"],
                        "site_id": state["site_id"]
                    }
                )
                
                if result.get("status") == "success":
                    all_personnel = result.get("items", [])
                    person = next((p for p in all_personnel if p.get("_id") == person_id), None)
                    if person:
                        personnel.append(person)
            except Exception:
                pass
        
        return {
            **state,
            "personnel": personnel,
            "status": "complete"
        }
    except Exception as e:
        return {
            **state,
            "personnel": [],
            "status": "complete",  # Don't fail the workflow
            "error": f"Failed to fetch personnel: {str(e)}"
        }


# Site Health Workflow

async def node_fetch_site_resources(state: SiteHealthState, mcp: MCPClient) -> SiteHealthState:
    """Fetch all resources for the site"""
    try:
        result = await mcp.call_tool(
            "query_site_overview",
            {
                "tenant_id": state["tenant_id"],
                "site_id": state["site_id"],
                "gateway_id": state.get("gateway_id")
            }
        )
        
        if result.get("status") == "success":
            return {
                **state,
                "cameras": result.get("cameras", []),
                "models": result.get("models", []),
                "profiles": result.get("profiles", []),
                "policies": result.get("policies", []),
                "cameras_active": result.get("counts", {}).get("cameras_active", 0),
                "cameras_inactive": result.get("counts", {}).get("cameras_inactive", 0),
                "status": "resources_fetched"
            }
        else:
            return {
                **state,
                "status": "error",
                "error": result.get("error", "Failed to fetch site resources")
            }
    except Exception as e:
        return {
            **state,
            "status": "error",
            "error": str(e)
        }


async def node_analyze_health(state: SiteHealthState, mcp: MCPClient) -> SiteHealthState:
    """Analyze site health and generate recommendations"""
    # Analysis logic remains same, synchronous part is fine in async func
    cameras = state.get("cameras", [])
    
    cameras_without_model = []
    cameras_without_policy = []
    cameras_without_profiles = []
    
    for camera in cameras:
        camera_id = camera.get("_id")
        bindings = camera.get("asset_info", {}).get("bindings", {})
        
        if not bindings.get("assigned_model_id"):
            cameras_without_model.append(camera_id)
        
        if not bindings.get("assigned_policy_id"):
            cameras_without_policy.append(camera_id)
        
        if not bindings.get("target_profile_ids"):
            cameras_without_profiles.append(camera_id)
    
    total_cameras = len(cameras)
    if total_cameras == 0:
        health_score = 100
    else:
        configured_cameras = total_cameras - len(set(
            cameras_without_model + cameras_without_policy + cameras_without_profiles
        ))
        health_score = int((configured_cameras / total_cameras) * 100)
    
    recommendations = []
    issues = []
    
    if cameras_without_model:
        recommendations.append(f"Assign AI models to {len(cameras_without_model)} cameras")
        issues.append({
            "type": "missing_model",
            "severity": "high",
            "camera_ids": cameras_without_model,
            "count": len(cameras_without_model)
        })
    
    if cameras_without_policy:
        recommendations.append(f"Assign alert policies to {len(cameras_without_policy)} cameras")
        issues.append({
            "type": "missing_policy",
            "severity": "high",
            "camera_ids": cameras_without_policy,
            "count": len(cameras_without_policy)
        })
    
    if cameras_without_profiles:
        recommendations.append(f"Assign detection profiles to {len(cameras_without_profiles)} cameras")
        issues.append({
            "type": "missing_profiles",
            "severity": "medium",
            "camera_ids": cameras_without_profiles,
            "count": len(cameras_without_profiles)
        })
    
    if state.get("cameras_inactive", 0) > 0:
        recommendations.append(f"Activate {state['cameras_inactive']} inactive cameras")
        issues.append({
            "type": "inactive_cameras",
            "severity": "medium",
            "count": state["cameras_inactive"]
        })
    
    if not recommendations:
        recommendations.append("Site is healthy - all cameras are properly configured")
    
    return {
        **state,
        "cameras_without_model": cameras_without_model,
        "cameras_without_policy": cameras_without_policy,
        "cameras_without_profiles": cameras_without_profiles,
        "health_score": health_score,
        "recommendations": recommendations,
        "issues": issues,
        "status": "complete"
    }


# PPE Configuration Status Workflow

async def node_fetch_cameras_and_ppe_resources(state: PPEConfigStatusState, mcp: MCPClient) -> PPEConfigStatusState:
    """Fetch cameras and PPE-related resources"""
    try:
        # Fetch cameras
        if state.get("location_filter"):
            camera_result = await mcp.call_tool(
                "query_cameras_by_location",
                {
                    "tenant_id": state["tenant_id"],
                    "site_id": state["site_id"],
                    "location": state["location_filter"],
                    "gateway_id": state.get("gateway_id")
                }
            )
        else:
            camera_result = await mcp.call_tool(
                "query_site_overview",
                {
                    "tenant_id": state["tenant_id"],
                    "site_id": state["site_id"],
                    "gateway_id": state.get("gateway_id")
                }
            )
        
        if camera_result.get("status") != "success":
            return {
                **state,
                "status": "error",
                "error": "Failed to fetch cameras"
            }
        
        cameras = camera_result.get("cameras", [])
        
        # Fetch PPE profiles
        profile_result = await mcp.call_tool(
            "list_profiles",
            {
                "tenant_id": state["tenant_id"],
                "site_id": state["site_id"]
            }
        )
        
        all_profiles = profile_result.get("items", []) if profile_result.get("status") == "success" else []
        ppe_profiles = [
            p for p in all_profiles
            if any(target.lower() in ["helmet", "vest", "ppe"] for target in p.get("targets", []))
        ]
        
        # Fetch PPE models
        model_result = await mcp.call_tool(
            "list_models",
            {
                "tenant_id": state["tenant_id"],
                "site_id": state["site_id"]
            }
        )
        
        all_models = model_result.get("items", []) if model_result.get("status") == "success" else []
        ppe_models = [
            m for m in all_models
            if "ppe" in m.get("name", "").lower()
        ]
        
        # Fetch PPE policies
        policy_result = await mcp.call_tool(
            "list_policy",
            {
                "tenant_id": state["tenant_id"],
                "site_id": state["site_id"],
                "anomaly_type": "PPE_VIOLATION"
            }
        )
        
        ppe_policies = policy_result.get("items", []) if policy_result.get("status") == "success" else []
        
        return {
            **state,
            "cameras": cameras,
            "ppe_profiles": ppe_profiles,
            "ppe_models": ppe_models,
            "ppe_policies": ppe_policies,
            "status": "resources_fetched"
        }
    except Exception as e:
        return {
            **state,
            "status": "error",
            "error": str(e)
        }


async def node_analyze_ppe_configuration(state: PPEConfigStatusState, mcp: MCPClient) -> PPEConfigStatusState:
    """Analyze PPE configuration status for each camera"""
    cameras = state.get("cameras", [])
    ppe_profile_ids = {p.get("_id") for p in state.get("ppe_profiles", [])}
    ppe_model_ids = {m.get("_id") for m in state.get("ppe_models", [])}
    ppe_policy_ids = {p.get("_id") for p in state.get("ppe_policies", [])}
    
    fully_configured = []
    partially_configured = []
    not_configured = []
    configuration_details = {}
    
    for camera in cameras:
        camera_id = camera.get("_id")
        bindings = camera.get("asset_info", {}).get("bindings", {})
        
        has_ppe_model = bindings.get("assigned_model_id") in ppe_model_ids
        has_ppe_profile = any(
            pid in ppe_profile_ids 
            for pid in bindings.get("target_profile_ids", [])
        )
        has_ppe_policy = bindings.get("assigned_policy_id") in ppe_policy_ids
        
        config_count = sum([has_ppe_model, has_ppe_profile, has_ppe_policy])
        
        configuration_details[camera_id] = {
            "has_ppe_model": has_ppe_model,
            "has_ppe_profile": has_ppe_profile,
            "has_ppe_policy": has_ppe_policy,
            "model_id": bindings.get("assigned_model_id"),
            "profile_ids": bindings.get("target_profile_ids", []),
            "policy_id": bindings.get("assigned_policy_id"),
            "location": camera.get("location"),
            "status": camera.get("status")
        }
        
        if config_count == 3:
            fully_configured.append(camera_id)
        elif config_count > 0:
            partially_configured.append(camera_id)
        else:
            not_configured.append(camera_id)
    
    return {
        **state,
        "fully_configured": fully_configured,
        "partially_configured": partially_configured,
        "not_configured": not_configured,
        "configuration_details": configuration_details,
        "status": "complete"
    }


# --- Graph Builders ---

def build_camera_full_context_graph(mcp: MCPClient):
    """Build the camera full context query workflow"""
    
    # Define async nodes directly wrapping the logic functions
    async def fetch_camera_node(state: CameraFullContextState):
        return await node_fetch_camera(state, mcp)
    
    async def fetch_personnel_node(state: CameraFullContextState):
        return await node_fetch_personnel(state, mcp)
    
    workflow = StateGraph(CameraFullContextState)
    
    workflow.add_node("fetch_camera", fetch_camera_node)
    workflow.add_node("fetch_personnel", fetch_personnel_node)
    
    workflow.set_entry_point("fetch_camera")
    workflow.add_edge("fetch_camera", "fetch_personnel")
    workflow.add_edge("fetch_personnel", END)
    
    return workflow.compile()


def build_site_health_graph(mcp: MCPClient):
    """Build the site health query workflow"""
    
    async def fetch_resources_node(state: SiteHealthState):
        return await node_fetch_site_resources(state, mcp)
    
    async def analyze_health_node(state: SiteHealthState):
        return await node_analyze_health(state, mcp)
    
    workflow = StateGraph(SiteHealthState)
    
    workflow.add_node("fetch_resources", fetch_resources_node)
    workflow.add_node("analyze_health", analyze_health_node)
    
    workflow.set_entry_point("fetch_resources")
    workflow.add_edge("fetch_resources", "analyze_health")
    workflow.add_edge("analyze_health", END)
    
    return workflow.compile()


def build_ppe_config_status_graph(mcp: MCPClient):
    """Build the PPE configuration status query workflow"""
    
    async def fetch_resources_node(state: PPEConfigStatusState):
        return await node_fetch_cameras_and_ppe_resources(state, mcp)
    
    async def analyze_config_node(state: PPEConfigStatusState):
        return await node_analyze_ppe_configuration(state, mcp)
    
    workflow = StateGraph(PPEConfigStatusState)
    
    workflow.add_node("fetch_resources", fetch_resources_node)
    workflow.add_node("analyze_config", analyze_config_node)
    
    workflow.set_entry_point("fetch_resources")
    workflow.add_edge("fetch_resources", "analyze_config")
    workflow.add_edge("analyze_config", END)
    
    return workflow.compile()


# --- Workflow Runners ---

async def run_camera_full_context_query(
    mcp: MCPClient,
    camera_id: str,
    tenant_id: str,
    site_id: str,
    gateway_id: str
) -> CameraFullContextState:
    """Run the camera full context query workflow"""
    app = build_camera_full_context_graph(mcp)
    
    initial_state: CameraFullContextState = {
        "camera_id": camera_id,
        "tenant_id": tenant_id,
        "site_id": site_id,
        "gateway_id": gateway_id,
        "status": "started"
    }
    
    # Ue ainvoke for async execution
    final_state = await app.ainvoke(initial_state)
    return final_state


async def run_site_health_query(
    mcp: MCPClient,
    tenant_id: str,
    site_id: str,
    gateway_id: Optional[str] = None
) -> SiteHealthState:
    """Run the site health query workflow"""
    app = build_site_health_graph(mcp)
    
    initial_state: SiteHealthState = {
        "tenant_id": tenant_id,
        "site_id": site_id,
        "gateway_id": gateway_id,
        "status": "started"
    }
    
    final_state = await app.ainvoke(initial_state)
    return final_state


async def run_ppe_config_status_query(
    mcp: MCPClient,
    tenant_id: str,
    site_id: str,
    gateway_id: Optional[str] = None,
    location_filter: Optional[str] = None
) -> PPEConfigStatusState:
    """Run the PPE configuration status query workflow"""
    app = build_ppe_config_status_graph(mcp)
    
    initial_state: PPEConfigStatusState = {
        "tenant_id": tenant_id,
        "site_id": site_id,
        "gateway_id": gateway_id,
        "location_filter": location_filter,
        "status": "started"
    }
    
    final_state = await app.ainvoke(initial_state)
    return final_state
