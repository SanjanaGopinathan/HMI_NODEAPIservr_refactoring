from typing import TypedDict, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from orchestrator.mcp_client import MCPClient


class CreateCameraState(TypedDict):
    """State for create_camera workflow"""
    # Input
    camera_id: str
    tenant_id: str
    site_id: str
    gateway_id: str
    name: str
    rtsp_url: str
    onvif_url: str
    location: Optional[str]
    zone: Optional[str]
    resolution: Optional[str]
    fps: Optional[int]
    userid: Optional[str]
    password: Optional[str]
    target_profile_ids: Optional[list[str]]
    assigned_policy_id: Optional[str]
    
    # Output
    camera: Optional[Dict]
    status: Optional[str]  # "exists", "created", "error"
    error_reason: Optional[str]


# --- Node implementations ---

async def node_check_camera_exists(state: CreateCameraState, mcp: MCPClient) -> CreateCameraState:
    """Check if camera already exists"""
    res = await mcp.call_tool(
        "list_cameras",
        {
            "tenant_id": state["tenant_id"],
            "site_id": state["site_id"],
            "gateway_id": state["gateway_id"],
            "limit": 200,
        }
    )
    
    cameras = res.get("cameras", [])
    existing = next((c for c in cameras if c.get("_id") == state["camera_id"]), None)
    
    if existing:
        state["status"] = "exists"
        state["camera"] = existing
        print(f"ℹ️  Camera '{state['camera_id']}' already exists")
    else:
        state["status"] = "create"
    
    return state


async def node_create_camera(state: CreateCameraState, mcp: MCPClient) -> CreateCameraState:
    """Create the camera"""
    # Build parameters, only including resolution/fps if provided
    params = {
        "camera_id": state["camera_id"],
        "tenant_id": state["tenant_id"],
        "site_id": state["site_id"],
        "gateway_id": state["gateway_id"],
        "name": state["name"],
        "rtsp_url": state["rtsp_url"],
        "onvif_url": state["onvif_url"],
        "status": "INACTIVE",  # Created as inactive by default
    }
    
    # Add optional parameters only if provided
    if state.get("location"):
        params["location"] = state["location"]
    if state.get("zone"):
        params["zone"] = state["zone"]
    if state.get("resolution"):
        params["resolution"] = state["resolution"]
    if state.get("fps"):
        params["fps"] = state["fps"]
    if state.get("userid"):
        params["userid"] = state["userid"]
    if state.get("password"):
        params["password"] = state["password"]
    if state.get("target_profile_ids"):
        params["target_profile_ids"] = state["target_profile_ids"]
    if state.get("assigned_policy_id"):
        params["assigned_policy_id"] = state["assigned_policy_id"]
    
    res = await mcp.call_tool("create_camera", params)
    
    if res.get("success"):
        state["camera"] = res.get("camera")
        state["status"] = "created"
        print(f"✅ Camera '{state['camera_id']}' created successfully")
    else:
        state["status"] = "error"
        state["error_reason"] = res.get("error", "Unknown error")
        print(f"❌ Failed to create camera '{state['camera_id']}': {state['error_reason']}")
    
    return state


# --- Graph builder ---

def build_create_camera_graph(mcp: MCPClient):
    """Build and compile the create_camera workflow"""
    builder = StateGraph(CreateCameraState)
    
    # Wrap nodes
    async def check_camera_exists_node(state: CreateCameraState) -> CreateCameraState:
        return await node_check_camera_exists(state, mcp)
    
    async def create_camera_node(state: CreateCameraState) -> CreateCameraState:
        return await node_create_camera(state, mcp)
    
    # Register nodes
    builder.add_node("check_camera_exists", check_camera_exists_node)
    builder.add_node("create_camera", create_camera_node)
    
    # Entry point
    builder.set_entry_point("check_camera_exists")
    
    # Conditional transitions
    def after_check_exists(state: CreateCameraState) -> str:
        if state.get("status") == "exists":
            return END
        return "create_camera"
    
    builder.add_conditional_edges("check_camera_exists", after_check_exists)
    builder.add_edge("create_camera", END)
    
    return builder.compile()


async def run_create_camera_workflow(
    mcp: MCPClient,
    camera_id: str,
    tenant_id: str,
    site_id: str,
    gateway_id: str,
    name: str,
    rtsp_url: str,
    onvif_url: str,
    location: Optional[str] = None,
    zone: Optional[str] = None,
    resolution: Optional[str] = None,
    fps: Optional[int] = None,
    userid: Optional[str] = None,
    password: Optional[str] = None,
    target_profile_ids: Optional[list[str]] = None,
    assigned_policy_id: Optional[str] = None,
) -> CreateCameraState:
    """Run the create_camera workflow"""
    app = build_create_camera_graph(mcp)
    
    initial_state: CreateCameraState = {
        "camera_id": camera_id,
        "tenant_id": tenant_id,
        "site_id": site_id,
        "gateway_id": gateway_id,
        "name": name,
        "rtsp_url": rtsp_url,
        "onvif_url": onvif_url,
        "location": location,
        "zone": zone,
        "resolution": resolution,
        "fps": fps,
        "userid": userid,
        "password": password,
        "target_profile_ids": target_profile_ids,
        "assigned_policy_id": assigned_policy_id,
    }
    
    final_state: CreateCameraState = await app.ainvoke(initial_state)
    return final_state
