from typing import TypedDict, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from orchestrator.mcp_client import MCPClient


class DeleteCameraState(TypedDict):
    """State for delete_camera workflow"""
    # Input
    camera_id: str
    tenant_id: str
    site_id: str
    gateway_id: str
    
    # Output
    status: Optional[str]  # "not_found", "deleted", "error"
    error_reason: Optional[str]


# --- Node implementations ---

async def node_check_camera_exists(state: DeleteCameraState, mcp: MCPClient) -> DeleteCameraState:
    """Check if camera exists before attempting deletion"""
    try:
        # Build query parameters
        query_params = {
            "tenant_id": state["tenant_id"],
            "site_id": state["site_id"],
            "gateway_id": state["gateway_id"],
            "limit": 200,
        }
        
        res = await mcp.call_tool("list_cameras", query_params)
        
        cameras = res.get("cameras", [])
        existing = next((c for c in cameras if c.get("_id") == state["camera_id"]), None)
        
        if existing:
            state["status"] = "exists"
            print(f"ℹ️  Camera '{state['camera_id']}' found, proceeding with deletion")
        else:
            state["status"] = "not_found"
            print(f"⚠️  Camera '{state['camera_id']}' not found")
        
        return state
    
    except Exception as e:
        state["status"] = "error"
        state["error_reason"] = f"Error checking camera existence: {str(e)}"
        print(f"❌ Error checking camera: {str(e)}")
        return state


async def node_delete_camera(state: DeleteCameraState, mcp: MCPClient) -> DeleteCameraState:
    """Delete the camera"""
    try:
        res = await mcp.call_tool(
            "delete_camera",
            {
                "camera_id": state["camera_id"],
                "tenant_id": state["tenant_id"],
                "site_id": state["site_id"],
                "gateway_id": state["gateway_id"]
            }
        )
        
        if res.get("success"):
            state["status"] = "deleted"
            print(f"✅ Camera '{state['camera_id']}' deleted successfully")
        else:
            state["status"] = "error"
            state["error_reason"] = res.get("error", "Unknown error during deletion")
            print(f"❌ Failed to delete camera '{state['camera_id']}': {state['error_reason']}")
        
        return state
    
    except Exception as e:
        state["status"] = "error"
        state["error_reason"] = str(e)
        print(f"❌ Exception during deletion: {str(e)}")
        return state


# --- Graph builder ---

def build_delete_camera_graph(mcp: MCPClient):
    """Build and compile the delete_camera workflow"""
    builder = StateGraph(DeleteCameraState)
    
    # Wrap nodes
    async def check_camera_exists_node(state: DeleteCameraState) -> DeleteCameraState:
        return await node_check_camera_exists(state, mcp)
    
    async def delete_camera_node(state: DeleteCameraState) -> DeleteCameraState:
        return await node_delete_camera(state, mcp)
    
    # Register nodes
    builder.add_node("check_camera_exists", check_camera_exists_node)
    builder.add_node("delete_camera", delete_camera_node)
    
    # Entry point
    builder.set_entry_point("check_camera_exists")
    
    # Conditional transitions
    def after_check_exists(state: DeleteCameraState) -> str:
        status = state.get("status")
        if status == "not_found" or status == "error":
            return END
        return "delete_camera"
    
    builder.add_conditional_edges("check_camera_exists", after_check_exists)
    builder.add_edge("delete_camera", END)
    
    return builder.compile()


async def run_delete_camera_workflow(
    mcp: MCPClient,
    camera_id: str,
    tenant_id: str,
    site_id: str,
    gateway_id: str,
) -> DeleteCameraState:
    """Run the delete_camera workflow
    
    Args:
        mcp: MCP client instance
        camera_id: Camera ID to delete
        tenant_id: Tenant ID for scoping and validation
        site_id: Site ID for scoping and validation
        gateway_id: Gateway ID for scoping and validation
    """
    app = build_delete_camera_graph(mcp)
    
    initial_state: DeleteCameraState = {
        "camera_id": camera_id,
        "tenant_id": tenant_id,
        "site_id": site_id,
        "gateway_id": gateway_id,
        "status": None,
        "error_reason": None,
    }
    
    final_state: DeleteCameraState = await app.ainvoke(initial_state)
    return final_state
