from typing import Any, Dict, List
from langgraph.graph import StateGraph, END
from .ppe_state import PPEConfigState
from orchestrator.mcp_client import MCPClient

# --- Node implementations ---

async def node_list_cameras(state: PPEConfigState, mcp: MCPClient) -> PPEConfigState:
    # Fetch cameras using available filters
    res = await mcp.call_tool(
        "list_cameras",
        {
            "tenant_id": state["tenant_id"],
            "site_id": state["site_id"],
            "gateway_id": state["gateway_id"],
            "location": state.get("location_filter"),
            "status": state.get("sensor_status"),
            "include_counts": True,
        },
    )
    
    cameras = res.get("cameras", [])
    
    # If camera_id is provided, filter to only that camera
    if state.get("camera_id"):
        camera_id = state["camera_id"]
        cameras = [c for c in cameras if c.get("_id") == camera_id]
    
    state["cameras"] = cameras
    if not cameras:
        state["status"] = "error"
        filter_used = state.get("camera_id") or state.get("location_filter") or "no filter"
        state["error_reason"] = f"No cameras matched the filter: {filter_used}"
    return state


async def node_select_cameras(state: PPEConfigState, mcp: MCPClient) -> PPEConfigState:
    state["camera_ids"] = [c["_id"] for c in state.get("cameras", [])]
    if not state["camera_ids"]:
        state["status"] = "error"
        state["error_reason"] = "No camera_ids derived from cameras"
    return state


async def node_find_ppe_profile(state: PPEConfigState, mcp: MCPClient) -> PPEConfigState:
    res = await mcp.call_tool(
        "list_profiles",
        {
            "tenant_id": state["tenant_id"],
            "site_id": state["site_id"],
            # Removed target_name_contains - filtering by name is done below
        },
    )
    profiles = res.get("detection_profiles", [])
    ppe_profile = next(
        (p for p in profiles if "PPE" in p.get("name", "").upper()),
        None,
    )
    state["ppe_profile"] = ppe_profile
    if not ppe_profile:
        state["status"] = "error"
        state["error_reason"] = "No PPE detection profile found"
    return state


async def node_assign_profile(state: PPEConfigState, mcp: MCPClient) -> PPEConfigState:
    if not state.get("camera_ids") or not state.get("ppe_profile"):
        state["status"] = "error"
        state["error_reason"] = "Missing cameras or PPE profile"
        return state

    # Use assign_profile MCP tool to update camera bindings via API
    res = await mcp.call_tool(
        "assign_profile",
        {
            "tenant_id": state["tenant_id"],
            "camera_ids": state["camera_ids"],
            "target_profile_ids": [state["ppe_profile"]["_id"]],
            "site_id": state["site_id"],
            "gateway_id": state["gateway_id"],
            "mode": "REPLACE"
        }
    )
    
    # Check for errors
    if res.get("status") == "error":
        state["status"] = "error"
        state["error_reason"] = res.get("error", "Failed to assign profile")
        return state
    
    state["assigned_profile_cameras"] = res.get("updated_camera_ids", [])
    return state


async def node_find_ppe_model(state: PPEConfigState, mcp: MCPClient) -> PPEConfigState:
    res = await mcp.call_tool(
        "list_models",
        {
            "tenant_id": state["tenant_id"],
            "site_id": state["site_id"],
            "framework_id": "openvino-2024.1",
            "status": "ACTIVE",
        },
    )
    models = res.get("models", [])
    ppe_model = next(
        (m for m in models if "PPE" in m.get("name", "").upper()),
        None,
    )
    state["ppe_model"] = ppe_model
    return state  # not an error if missing; we handle later


async def node_assign_model(state: PPEConfigState, mcp: MCPClient) -> PPEConfigState:
    if not state.get("ppe_model"):
        return state  # skip

    if not state.get("camera_ids"):
        state["status"] = "error"
        state["error_reason"] = "No cameras to assign model"
        return state

    # Use assign_cameras_to_model MCP tool to update camera bindings via API
    res = await mcp.call_tool(
        "assign_cameras_to_model",
        {
            "tenant_id": state["tenant_id"],
            "camera_ids": state["camera_ids"],
            "model_id": state["ppe_model"]["_id"],
            "site_id": state["site_id"],
            "gateway_id": state["gateway_id"],
            "auto_adjust_stream_profile": False
        }
    )
    
    # Check for errors
    if res.get("status") == "error":
        state["status"] = "error"
        state["error_reason"] = res.get("error", "Failed to assign model")
        return state
    
    state["assigned_model_cameras"] = res.get("assigned_camera_ids", [])
    return state


async def node_find_ppe_policy(state: PPEConfigState, mcp: MCPClient) -> PPEConfigState:
    res = await mcp.call_tool(
        "list_policy",
        {
            "tenant_id": state["tenant_id"],
            "anomaly_type": "PPE_VIOLATION",
            "site_id": state["site_id"]            
        },
    )
    policy = res.get("policies", [])
    ppe_policy = next(
        (m for m in policy if "PPE_VIOLATION" in m.get("anomaly_type", "").upper()),
        None,
    )
    state["policy"] = ppe_policy
    return state  # not an error if missing; we handle later

async def node_set_policy(state: PPEConfigState, mcp: MCPClient) -> PPEConfigState:
    if not state.get("camera_ids") or not state.get("policy"):
        state["status"] = "error"
        state["error_reason"] = "Missing cameras or PPE policy"
        return state

    # Use set_alert_policy MCP tool to update camera bindings via API
    res = await mcp.call_tool(
        "set_alert_policy",
        {
            "tenant_id": state["tenant_id"],
            "camera_ids": state["camera_ids"],
            "policy_id": state["policy"]["_id"],
            "site_id": state["site_id"],
            "gateway_id": state["gateway_id"]
        }
    )
    
    # Check for errors
    if res.get("status") == "error":
        state["status"] = "error"
        state["error_reason"] = res.get("error", "Failed to assign policy")
        return state
    
    state["assigned_policy_cameras"] = res.get("assigned_camera_ids", [])
    return state

async def node_activate_cameras(state: PPEConfigState, mcp: MCPClient) -> PPEConfigState:
    if not state.get("camera_ids"):
        state["status"] = "error"
        state["error_reason"] = "Missing cameras"
        return state

    # Use update_camera MCP tool to activate cameras via API
    status_updated_cameras = []
    status_update_failed = []
    mapping_activated_cameras = []
    mapping_activation_failed = []
    
    for camera_id in state["camera_ids"]:
        res = await mcp.call_tool(
            "update_camera",
            {
                "camera_id": camera_id,
                "tenant_id": state["tenant_id"],
                "site_id": state["site_id"],
                "gateway_id": state["gateway_id"],
                "status": "ACTIVE"
            }
        )
        
        # Check for errors
        if res.get("success"):
            status_updated_cameras.append(camera_id)
            print(f"? Successfully updated camera status to ACTIVE: {camera_id}")
            
            # Update camera object in state with the updated version from API
            updated_camera = res.get("camera")
            if updated_camera:
                for i, camera in enumerate(state.get("cameras", [])):
                    if camera.get("_id") == camera_id:
                        state["cameras"][i] = updated_camera
                        break
            
            # After successful status update, activate camera (map to legacy DT_ConfigStorage)
            print(f"?? Activating camera mapping for: {camera_id}")
            activate_res = await mcp.call_tool(
                "activate_camera",
                {
                    "camera_id": camera_id,
                    "tenant_id": state["tenant_id"],
                    "site_id": state["site_id"],
                    "gateway_id": state["gateway_id"]
                }
            )
            
            if activate_res.get("success"):
                mapping_activated_cameras.append(camera_id)
                sensor_id = activate_res.get("sensor_id")
                subscriber_ids = activate_res.get("subscriber_ids", [])
                print(f"? Successfully activated camera mapping {camera_id}")
                print(f"   ? Mapped to sensor: {sensor_id}")
                print(f"   ? Created subscribers: {', '.join(subscriber_ids)}")
            else:
                mapping_activation_failed.append(camera_id)
                print(f"? Failed to activate camera mapping {camera_id}: {activate_res.get('error')}")
        else:
            status_update_failed.append(camera_id)
            print(f"? Failed to update camera status {camera_id}: {res.get('error')}")
    
    state["status_updated_cameras"] = status_updated_cameras
    state["status_update_failed"] = status_update_failed
    state["mapping_activated_cameras"] = mapping_activated_cameras
    state["mapping_activation_failed"] = mapping_activation_failed
    state["sensor_status"] = "ACTIVE"
    
    # Log summary
    print(f"\n?? Activation Summary:")
    print(f"   Total cameras: {len(state['camera_ids'])}")
    print(f"   Status updated: {len(status_updated_cameras)}")
    print(f"   Status update failed: {len(status_update_failed)}")
    print(f"   Mapping activated: {len(mapping_activated_cameras)}")
    print(f"   Mapping activation failed: {len(mapping_activation_failed)}")
    
    return state

# --- Graph builder ---

def build_configure_ppe_graph(mcp: MCPClient):
    """
    Build and compile the LangGraph workflow for 'Enable PPE monitoring'.
    Returns a compiled app that supports .invoke() / .ainvoke().
    """
    builder = StateGraph(PPEConfigState)

    # Wrap each node_* function in an async closure that binds mcp

    async def list_cameras_node(state: PPEConfigState) -> PPEConfigState:
        return await node_list_cameras(state, mcp)

    async def select_cameras_node(state: PPEConfigState) -> PPEConfigState:
        return await node_select_cameras(state, mcp)

    async def find_ppe_profile_node(state: PPEConfigState) -> PPEConfigState:
        return await node_find_ppe_profile(state, mcp)

    async def assign_profile_node(state: PPEConfigState) -> PPEConfigState:
        return await node_assign_profile(state, mcp)

    async def find_ppe_model_node(state: PPEConfigState) -> PPEConfigState:
        return await node_find_ppe_model(state, mcp)

    async def assign_model_node(state: PPEConfigState) -> PPEConfigState:
        return await node_assign_model(state, mcp)
    
    async def find_ppe_policy_node(state: PPEConfigState) -> PPEConfigState:
        return await node_find_ppe_policy(state, mcp)

    async def set_policy_node(state: PPEConfigState) -> PPEConfigState:
        return await node_set_policy(state, mcp)
    
    async def activate_cameras_node(state: PPEConfigState) -> PPEConfigState:
        return await node_activate_cameras(state, mcp)

    # Register nodes with LangGraph
    builder.add_node("list_cameras", list_cameras_node)
    builder.add_node("select_cameras", select_cameras_node)
    builder.add_node("find_ppe_profile", find_ppe_profile_node)
    builder.add_node("assign_profile", assign_profile_node)
    builder.add_node("find_ppe_model", find_ppe_model_node)
    builder.add_node("assign_model", assign_model_node)
    builder.add_node("find_ppe_policy", find_ppe_policy_node)
    builder.add_node("set_policy", set_policy_node)
    builder.add_node("activate_cameras", activate_cameras_node)

    # Entry point
    builder.set_entry_point("list_cameras")

    # Conditional transitions

    def after_list_cameras(state: PPEConfigState) -> str:
        if state.get("status") == "error":
            return END
        return "select_cameras"

    def after_select_cameras(state: PPEConfigState) -> str:
        if state.get("status") == "error":
            return END
        return "find_ppe_profile"

    def after_find_ppe_profile(state: PPEConfigState) -> str:
        if state.get("status") == "error":
            return END
        return "assign_profile"

    builder.add_conditional_edges("list_cameras", after_list_cameras)
    builder.add_conditional_edges("select_cameras", after_select_cameras)
    builder.add_conditional_edges("find_ppe_profile", after_find_ppe_profile)

    builder.add_edge("assign_profile", "find_ppe_model")

    def after_find_ppe_model(state: PPEConfigState) -> str:
        if state.get("ppe_model"):
            return "assign_model"
        return "find_ppe_policy"

    def after_assign_model(state: PPEConfigState) -> str:
        if state.get("status") == "error":
            return END
        return "find_ppe_policy"
    
    builder.add_conditional_edges("find_ppe_model", after_find_ppe_model)
    builder.add_conditional_edges("assign_model", after_assign_model)
    builder.add_edge("find_ppe_policy", "set_policy")
    builder.add_edge("set_policy", "activate_cameras")
    builder.add_edge("activate_cameras", END)

    '''TBD - Post this DB upsert of camera sensor into HMI DB needs to be handled here.
    1. Pass the asset JSON payload to API server
    2. API server of HMI 1.0 shall perform LCD to map data from new model to old model
    3. Post upsert of camera sensor, channel module shall trigger streaming and inference
    '''

    # Compile to a runnable app
    app = builder.compile()
    return app


async def run_configure_ppe_workflow(
    mcp: MCPClient,
    tenant_id: str,
    site_id: str,
    gateway_id: str,
    camera_id: str = None,
    location_filter: str = None,
    status: str = "INACTIVE"
) -> PPEConfigState:
    """
    Run the compiled Configure PPE workflow and return final state.
    
    Args:
        camera_id: Optional specific camera ID to configure
        location_filter: Optional location filter for cameras
        At least one of camera_id or location_filter must be provided
    """
    app = build_configure_ppe_graph(mcp)

    initial_state: PPEConfigState = {
        "tenant_id": tenant_id,
        "site_id": site_id,
        "gateway_id": gateway_id,
        "sensor_status": status
    }
    
    # Add camera_id or location_filter based on what's provided
    if camera_id:
        initial_state["camera_id"] = camera_id
    if location_filter:
        initial_state["location_filter"] = location_filter

    # For async support in LangGraph
    final_state: PPEConfigState = await app.ainvoke(initial_state)
    return final_state
