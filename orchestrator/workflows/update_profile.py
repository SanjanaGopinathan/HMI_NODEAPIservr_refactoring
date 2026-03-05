from typing import TypedDict, Optional, Dict, List
from langgraph.graph import StateGraph, END
from orchestrator.mcp_client import MCPClient

class UpdateProfileState(TypedDict):
    """State for update_profile workflow"""
    # Input
    profile_id: str
    tenant_id: str
    site_id: str
    gateway_id: str
    name: Optional[str]
    targets: Optional[List[str]]
    
    # Internal
    existing_profile: Optional[Dict]
    
    # Output
    result: Optional[Dict]
    status: Optional[str]  # "updated", "error", "not_found"
    error_reason: Optional[str]


async def node_check_exists(state: UpdateProfileState, mcp: MCPClient) -> UpdateProfileState:
    """Check if profile exists"""
    try:
        res = await mcp.call_tool(
            "list_profiles",
            {
                "tenant_id": state["tenant_id"],
                "site_id": state["site_id"],
            }
        )
        profiles = res.get("detection_profiles", [])
        existing = next(
            (p for p in profiles if p.get("_id") == state["profile_id"] or p.get("id") == state["profile_id"]),
            None
        )
        
        if existing:
            state["existing_profile"] = existing
            state["status"] = "found"
        else:
            state["status"] = "not_found"
            state["error_reason"] = f"Profile {state['profile_id']} not found"
            
    except Exception as e:
        state["status"] = "error"
        state["error_reason"] = str(e)
        
    return state


async def node_delete_old(state: UpdateProfileState, mcp: MCPClient) -> UpdateProfileState:
    """Delete the old profile"""
    try:
        # Optimistically try delete_profile
        await mcp.call_tool(
            "delete_profile",
            {
                "profile_id": state["profile_id"],
                "tenant_id": state["tenant_id"],
                "site_id": state["site_id"],
                "gateway_id": state["gateway_id"]
            }
        )
    except Exception as e:
        print(f"Warning: delete_profile failed or not found: {e}")
        # Identify if we should stop or proceed?
        # If delete fails, create might fail if it enforces uniqueness.
        # But we proceed and see.
        pass
        
    return state


async def node_create_new(state: UpdateProfileState, mcp: MCPClient) -> UpdateProfileState:
    """Create the new profile with updated data"""
    existing = state["existing_profile"]
    
    # Merge existing data with updates
    new_name = state["name"] if state["name"] else existing.get("name")
    new_targets = state["targets"] if state["targets"] is not None else existing.get("targets", [])
    
    try:
        res = await mcp.call_tool(
            "create_profile",
            {
                "profile_id": state["profile_id"],
                "tenant_id": state["tenant_id"],
                "site_id": state["site_id"],
                "gateway_id": state["gateway_id"],
                "name": new_name,
                "targets": new_targets
            }
        )
        
        if res.get("success"):
            state["result"] = res.get("profile")
            state["status"] = "updated"
        else:
            state["status"] = "error"
            state["error_reason"] = res.get("error", "Failed to recreate profile")
            
    except Exception as e:
        state["status"] = "error"
        state["error_reason"] = str(e)
        
    return state


def build_update_profile_graph(mcp: MCPClient):
    builder = StateGraph(UpdateProfileState)
    
    async def check_node(state): return await node_check_exists(state, mcp)
    async def delete_node(state): return await node_delete_old(state, mcp)
    async def create_node(state): return await node_create_new(state, mcp)
    
    builder.add_node("check_exists", check_node)
    builder.add_node("delete_old", delete_node)
    builder.add_node("create_new", create_node)
    
    builder.set_entry_point("check_exists")
    
    def after_check(state):
        if state["status"] == "not_found" or state["status"] == "error":
            return END
        return "delete_old"
    
    builder.add_conditional_edges("check_exists", after_check)
    builder.add_edge("delete_old", "create_new")
    builder.add_edge("create_new", END)
    
    return builder.compile()


async def run_update_profile_workflow(mcp: MCPClient, **kwargs) -> UpdateProfileState:
    app = build_update_profile_graph(mcp)
    initial_state = UpdateProfileState(
        profile_id=kwargs["profile_id"],
        tenant_id=kwargs.get("tenant_id"),
        site_id=kwargs.get("site_id"),
        gateway_id=kwargs.get("gateway_id"),
        name=kwargs.get("name"),
        targets=kwargs.get("targets"),
        existing_profile=None,
        result=None,
        status="start",
        error_reason=None
    )
    return await app.ainvoke(initial_state)
