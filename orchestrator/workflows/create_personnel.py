from typing import TypedDict, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from orchestrator.mcp_client import MCPClient


class CreatePersonnelState(TypedDict):
    """State for create_personnel workflow"""
    # Input
    person_id: str
    tenant_id: str
    site_id: str
    name: str
    role: str
    phone: Optional[str]
    email: Optional[str]
    sip_uri: Optional[str]
    on_call: bool
    status: str
    
    # Output
    personnel: Optional[Dict]
    status_result: Optional[str]  # "exists", "created", "error"
    error_reason: Optional[str]


# --- Node implementations ---

async def node_check_personnel_exists(state: CreatePersonnelState, mcp: MCPClient) -> CreatePersonnelState:
    """Check if personnel already exists"""
    res = await mcp.call_tool(
        "list_personnel",
        {
            "tenant_id": state["tenant_id"],
            "site_id": state["site_id"],
        }
    )
    
    personnel_list = res.get("personnel", [])
    # Check by ID or by name
    existing = next(
        (p for p in personnel_list if p.get("_id") == state["person_id"] or p.get("name") == state["name"]),
        None
    )
    
    if existing:
        state["status_result"] = "exists"
        state["personnel"] = existing
        print(f"ℹ️  Personnel '{state['person_id']}' already exists")
    else:
        state["status_result"] = "create"
    
    return state


async def node_create_personnel(state: CreatePersonnelState, mcp: MCPClient) -> CreatePersonnelState:
    """Create the personnel record"""
    # Build arguments for create_personnel tool
    args = {
        "person_id": state["person_id"],
        "tenant_id": state["tenant_id"],
        "site_id": state["site_id"],
        "name": state["name"],
        "role": state["role"],
        "on_call": state.get("on_call", False),
        "status": state.get("status", "ACTIVE"),
    }
    
    # Add optional contact fields
    if state.get("phone"):
        args["phone"] = state["phone"]
    if state.get("email"):
        args["email"] = state["email"]
    if state.get("sip_uri"):
        args["sip_uri"] = state["sip_uri"]
    
    res = await mcp.call_tool("create_personnel", args)
    
    if res.get("success"):
        state["personnel"] = res.get("personnel")
        state["status_result"] = "created"
        print(f"✅ Personnel '{state['person_id']}' created successfully")
    else:
        state["status_result"] = "error"
        state["error_reason"] = res.get("error", "Unknown error")
        print(f"❌ Failed to create personnel '{state['person_id']}': {state['error_reason']}")
    
    return state


# --- Graph builder ---

def build_create_personnel_graph(mcp: MCPClient):
    """Build and compile the create_personnel workflow"""
    builder = StateGraph(CreatePersonnelState)
    
    # Wrap nodes
    async def check_personnel_exists_node(state: CreatePersonnelState) -> CreatePersonnelState:
        return await node_check_personnel_exists(state, mcp)
    
    async def create_personnel_node(state: CreatePersonnelState) -> CreatePersonnelState:
        return await node_create_personnel(state, mcp)
    
    # Register nodes
    builder.add_node("check_personnel_exists", check_personnel_exists_node)
    builder.add_node("create_personnel", create_personnel_node)
    
    # Entry point
    builder.set_entry_point("check_personnel_exists")
    
    # Conditional transitions
    def after_check_exists(state: CreatePersonnelState) -> str:
        if state.get("status_result") == "exists":
            return END
        return "create_personnel"
    
    builder.add_conditional_edges("check_personnel_exists", after_check_exists)
    builder.add_edge("create_personnel", END)
    
    return builder.compile()


async def run_create_personnel_workflow(
    mcp: MCPClient,
    person_id: str,
    tenant_id: str,
    site_id: str,
    name: str,
    role: str,
    phone: Optional[str] = None,
    email: Optional[str] = None,
    sip_uri: Optional[str] = None,
    on_call: bool = False,
    status: str = "ACTIVE",
) -> CreatePersonnelState:
    """Run the create_personnel workflow"""
    app = build_create_personnel_graph(mcp)
    
    initial_state: CreatePersonnelState = {
        "person_id": person_id,
        "tenant_id": tenant_id,
        "site_id": site_id,
        "name": name,
        "role": role,
        "phone": phone,
        "email": email,
        "sip_uri": sip_uri,
        "on_call": on_call,
        "status": status,
    }
    
    final_state: CreatePersonnelState = await app.ainvoke(initial_state)
    return final_state
