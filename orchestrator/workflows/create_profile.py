from typing import TypedDict, Optional, Dict, Any, List
from langgraph.graph import StateGraph, END
from orchestrator.mcp_client import MCPClient


class CreateProfileState(TypedDict):
    """State for create_profile workflow"""
    # Input
    profile_id: str
    tenant_id: str
    site_id: str
    gateway_id: str
    name: str
    targets: List[str]
    
    # Output
    profile: Optional[Dict]
    status: Optional[str]  # "exists", "created", "error"
    error_reason: Optional[str]


# --- Node implementations ---

async def node_check_profile_exists(state: CreateProfileState, mcp: MCPClient) -> CreateProfileState:
    """Check if profile already exists"""
    res = await mcp.call_tool(
        "list_profiles",
        {
            "tenant_id": state["tenant_id"],
            "site_id": state["site_id"],
        }
    )
    
    profiles = res.get("detection_profiles", [])
    # Check by ID or by name
    existing = next(
        (p for p in profiles if p.get("_id") == state["profile_id"] or p.get("name") == state["name"]),
        None
    )
    
    if existing:
        state["status"] = "exists"
        state["profile"] = existing
        print(f"ℹ️  Profile '{state['profile_id']}' already exists")
    else:
        state["status"] = "create"
    
    return state


async def node_create_profile(state: CreateProfileState, mcp: MCPClient) -> CreateProfileState:
    """Create the detection profile"""
    res = await mcp.call_tool(
        "create_profile",
        {
            "profile_id": state["profile_id"],
            "tenant_id": state["tenant_id"],
            "site_id": state["site_id"],
            "gateway_id": state["gateway_id"], # Added gateway_id
            "name": state["name"],
            "targets": state.get("targets", []), # Changed to use .get with default
        }
    )
    
    if res.get("success"):
        state["profile"] = res.get("profile")
        state["status"] = "created"
        print(f"✅ Profile '{state['profile_id']}' created successfully")
    else:
        state["status"] = "error"
        state["error_reason"] = res.get("error", "Unknown error")
        print(f"❌ Failed to create profile '{state['profile_id']}': {state['error_reason']}")
    
    return state


# --- Graph builder ---

def build_create_profile_graph(mcp: MCPClient):
    """Build and compile the create_profile workflow"""
    builder = StateGraph(CreateProfileState)
    
    # Wrap nodes
    async def check_profile_exists_node(state: CreateProfileState) -> CreateProfileState:
        return await node_check_profile_exists(state, mcp)
    
    async def create_profile_node(state: CreateProfileState) -> CreateProfileState:
        return await node_create_profile(state, mcp)
    
    # Register nodes
    builder.add_node("check_profile_exists", check_profile_exists_node)
    builder.add_node("create_profile", create_profile_node)
    
    # Entry point
    builder.set_entry_point("check_profile_exists")
    
    # Conditional transitions
    def after_check_exists(state: CreateProfileState) -> str:
        if state.get("status") == "exists":
            return END
        return "create_profile"
    
    builder.add_conditional_edges("check_profile_exists", after_check_exists)
    builder.add_edge("create_profile", END)
    
    return builder.compile()


async def run_create_profile_workflow(
    mcp: MCPClient,
    profile_id: str,
    tenant_id: str,
    site_id: str,
    gateway_id: str,
    name: str,
    targets: List[str],
) -> CreateProfileState:
    """Run the create_profile workflow"""
    app = build_create_profile_graph(mcp)
    
    initial_state: CreateProfileState = {
        "profile_id": profile_id,
        "tenant_id": tenant_id,
        "site_id": site_id,
        "gateway_id": gateway_id,
        "name": name,
        "targets": targets,
    }
    
    final_state: CreateProfileState = await app.ainvoke(initial_state)
    return final_state
