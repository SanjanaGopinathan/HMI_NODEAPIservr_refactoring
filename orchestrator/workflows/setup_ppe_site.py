from typing import TypedDict, Optional, Dict, Any, List
from langgraph.graph import StateGraph, END
from orchestrator.mcp_client import MCPClient
from orchestrator.workflows.create_camera import run_create_camera_workflow
from orchestrator.workflows.create_profile import run_create_profile_workflow
from orchestrator.workflows.create_policy import run_create_policy_workflow
from orchestrator.workflows.configure_ppe import run_configure_ppe_workflow


class SetupPPESiteState(TypedDict):
    """State for setup_ppe_site workflow"""
    # Input
    tenant_id: str
    site_id: str
    gateway_id: str
    cameras_config: List[Dict[str, Any]]  # Camera configurations
    personnel_ids: List[str]  # For alert routing
    
    # Output
    created_cameras: Optional[List[str]]
    created_profile: Optional[str]
    created_policy: Optional[str]
    configured_cameras: Optional[List[str]]
    status: Optional[str]  # "success", "partial", "error"
    error_reason: Optional[str]


# --- Node implementations ---

async def node_create_cameras(state: SetupPPESiteState, mcp: MCPClient) -> SetupPPESiteState:
    """Create all cameras"""
    created = []
    
    for cam_config in state.get("cameras_config", []):
        try:
            result = await run_create_camera_workflow(
                mcp=mcp,
                camera_id=cam_config["camera_id"],
                tenant_id=state["tenant_id"],
                site_id=state["site_id"],
                gateway_id=state["gateway_id"],
                name=cam_config["name"],
                rtsp_url=cam_config["rtsp_url"],
                onvif_url=cam_config["onvif_url"],
                location=cam_config.get("location"),
                zone=cam_config.get("zone"),
            )
            
            if result.get("status") in ["created", "exists"]:
                created.append(cam_config["camera_id"])
        except Exception as e:
            print(f"⚠️  Failed to create camera {cam_config.get('camera_id')}: {e}")
    
    state["created_cameras"] = created
    print(f"\n📷 Created/verified {len(created)} cameras")
    return state


async def node_create_ppe_profile(state: SetupPPESiteState, mcp: MCPClient) -> SetupPPESiteState:
    """Create PPE detection profile"""
    try:
        result = await run_create_profile_workflow(
            mcp=mcp,
            profile_id=f"PROFILE_PPE_{state['site_id']}",
            tenant_id=state["tenant_id"],
            site_id=state["site_id"],
            name="PPE Detection",
            targets=["helmet", "vest", "person"],
        )
        
        if result.get("status") in ["created", "exists"]:
            state["created_profile"] = result.get("profile", {}).get("_id")
            print(f"✅ PPE profile ready: {state['created_profile']}")
    except Exception as e:
        print(f"⚠️  Failed to create PPE profile: {e}")
    
    return state


async def node_create_alert_policy(state: SetupPPESiteState, mcp: MCPClient) -> SetupPPESiteState:
    """Create PPE alert policy"""
    try:
        result = await run_create_policy_workflow(
            mcp=mcp,
            policy_id=f"POLICY_PPE_{state['gateway_id']}",
            tenant_id=state["tenant_id"],
            site_id=state["site_id"],
            anomaly_type="PPE_VIOLATION",
            severity_levels=["WARNING", "CRITICAL"],
            channels=["EMAIL", "SIP_PTT", "HMI_POPUP"],
            person_ids=state.get("personnel_ids", []),
            min_severity="WARNING",
            enabled=True,
        )
        
        if result.get("status") in ["created", "exists"]:
            state["created_policy"] = result.get("policy", {}).get("_id")
            print(f"✅ Alert policy ready: {state['created_policy']}")
    except Exception as e:
        print(f"⚠️  Failed to create alert policy: {e}")
    
    return state


async def node_configure_cameras(state: SetupPPESiteState, mcp: MCPClient) -> SetupPPESiteState:
    """Configure cameras with profile, model, and policy"""
    if not state.get("created_cameras"):
        state["status"] = "error"
        state["error_reason"] = "No cameras to configure"
        return state
    
    try:
        # Run the existing configure_ppe_workflow
        # This will assign profile, model, policy and activate cameras
        result = await run_configure_ppe_workflow(
            mcp=mcp,
            tenant_id=state["tenant_id"],
            site_id=state["site_id"],
            gateway_id=state["gateway_id"],
            location_filter="",  # No filter, configure all cameras
            status="INACTIVE",  # Configure inactive cameras
        )
        
        if result.get("status") != "error":
            state["configured_cameras"] = result.get("activated_cameras", [])
            state["status"] = "success"
            print(f"\n🎉 Successfully configured {len(state['configured_cameras'])} cameras")
        else:
            state["status"] = "partial"
            state["error_reason"] = result.get("error_reason")
            print(f"⚠️  Configuration completed with errors: {state['error_reason']}")
    except Exception as e:
        state["status"] = "error"
        state["error_reason"] = str(e)
        print(f"❌ Failed to configure cameras: {e}")
    
    return state


# --- Graph builder ---

def build_setup_ppe_site_graph(mcp: MCPClient):
    """Build and compile the setup_ppe_site workflow"""
    builder = StateGraph(SetupPPESiteState)
    
    # Wrap nodes
    async def create_cameras_node(state: SetupPPESiteState) -> SetupPPESiteState:
        return await node_create_cameras(state, mcp)
    
    async def create_ppe_profile_node(state: SetupPPESiteState) -> SetupPPESiteState:
        return await node_create_ppe_profile(state, mcp)
    
    async def create_alert_policy_node(state: SetupPPESiteState) -> SetupPPESiteState:
        return await node_create_alert_policy(state, mcp)
    
    async def configure_cameras_node(state: SetupPPESiteState) -> SetupPPESiteState:
        return await node_configure_cameras(state, mcp)
    
    # Register nodes
    builder.add_node("create_cameras", create_cameras_node)
    builder.add_node("create_ppe_profile", create_ppe_profile_node)
    builder.add_node("create_alert_policy", create_alert_policy_node)
    builder.add_node("configure_cameras", configure_cameras_node)
    
    # Entry point
    builder.set_entry_point("create_cameras")
    
    # Linear flow
    builder.add_edge("create_cameras", "create_ppe_profile")
    builder.add_edge("create_ppe_profile", "create_alert_policy")
    builder.add_edge("create_alert_policy", "configure_cameras")
    builder.add_edge("configure_cameras", END)
    
    return builder.compile()


async def run_setup_ppe_site_workflow(
    mcp: MCPClient,
    tenant_id: str,
    site_id: str,
    gateway_id: str,
    cameras_config: List[Dict[str, Any]],
    personnel_ids: Optional[List[str]] = None,
) -> SetupPPESiteState:
    """
    Run the complete PPE site setup workflow.
    
    This workflow:
    1. Creates cameras (if they don't exist)
    2. Creates PPE detection profile (if it doesn't exist)
    3. Creates alert policy (if it doesn't exist)
    4. Configures cameras with profile, model, and policy
    5. Activates cameras
    """
    app = build_setup_ppe_site_graph(mcp)
    
    initial_state: SetupPPESiteState = {
        "tenant_id": tenant_id,
        "site_id": site_id,
        "gateway_id": gateway_id,
        "cameras_config": cameras_config,
        "personnel_ids": personnel_ids or [],
    }
    
    print(f"\n🚀 Starting PPE site setup for {site_id}")
    print(f"   Cameras to create: {len(cameras_config)}")
    print(f"   Personnel for alerts: {len(personnel_ids or [])}\n")
    
    final_state: SetupPPESiteState = await app.ainvoke(initial_state)
    return final_state
