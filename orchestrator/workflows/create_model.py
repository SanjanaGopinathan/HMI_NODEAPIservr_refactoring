from typing import TypedDict, Optional, Dict, Any, List
from langgraph.graph import StateGraph, END
from orchestrator.mcp_client import MCPClient


class CreateModelState(TypedDict):
    """State for create_model workflow"""
    # Input
    model_id: str
    tenant_id: str
    site_id: str
    gateway_id: str
    name: str
    framework_id: str
    supported_profile_ids: Optional[List[str]]
    status: Optional[str]
    
    # Output
    model: Optional[Dict]
    workflow_status: Optional[str]  # "exists", "created", "error"
    error_reason: Optional[str]


# --- Node implementations ---

async def node_check_model_exists(state: CreateModelState, mcp: MCPClient) -> CreateModelState:
    """Check if model already exists"""
    res = await mcp.call_tool(
        "list_models",
        {
            "tenant_id": state["tenant_id"],
            "site_id": state["site_id"],
            "status": "", # List all statuses
        }
    )
    
    models = res.get("models", [])
    # Check by ID or by name
    existing = next(
        (m for m in models if m.get("_id") == state["model_id"] or m.get("name") == state["name"]),
        None
    )
    
    if existing:
        state["workflow_status"] = "exists"
        state["model"] = existing
        print(f"ℹ️  Model '{state['model_id']}' already exists")
    else:
        state["workflow_status"] = "create"
    
    return state


async def node_create_model(state: CreateModelState, mcp: MCPClient) -> CreateModelState:
    """Create the AI model"""
    res = await mcp.call_tool(
        "create_model",
        {
            "model_id": state["model_id"],
            "tenant_id": state["tenant_id"],
            "site_id": state["site_id"],
            "gateway_id": state["gateway_id"],
            "name": state["name"],
            "framework_id": state["framework_id"],
            "supported_profile_ids": state.get("supported_profile_ids", []),
            "status": state.get("status", "ACTIVE"),
        }
    )
    
    if res.get("success"):
        state["model"] = res.get("model")
        state["workflow_status"] = "created"
        print(f"✅ Model '{state['model_id']}' created successfully")
    else:
        state["workflow_status"] = "error"
        state["error_reason"] = res.get("error", "Unknown error")
        print(f"❌ Failed to create model '{state['model_id']}': {state['error_reason']}")
    
    return state


# --- Graph builder ---

def build_create_model_graph(mcp: MCPClient):
    """Build and compile the create_model workflow"""
    builder = StateGraph(CreateModelState)
    
    # Wrap nodes
    async def check_model_exists_node(state: CreateModelState) -> CreateModelState:
        return await node_check_model_exists(state, mcp)
    
    async def create_model_node(state: CreateModelState) -> CreateModelState:
        return await node_create_model(state, mcp)
    
    # Register nodes
    builder.add_node("check_model_exists", check_model_exists_node)
    builder.add_node("create_model", create_model_node)
    
    # Entry point
    builder.set_entry_point("check_model_exists")
    
    # Conditional transitions
    def after_check_exists(state: CreateModelState) -> str:
        if state.get("workflow_status") == "exists":
            return END
        return "create_model"
    
    builder.add_conditional_edges("check_model_exists", after_check_exists)
    builder.add_edge("create_model", END)
    
    return builder.compile()


async def run_create_model_workflow(
    mcp: MCPClient,
    model_id: str,
    tenant_id: str,
    site_id: str,
    gateway_id: str,
    name: str,
    framework_id: str,
    supported_profile_ids: Optional[List[str]] = None,
    status: str = "ACTIVE",
) -> CreateModelState:
    """Run the create_model workflow"""
    app = build_create_model_graph(mcp)
    
    initial_state: CreateModelState = {
        "model_id": model_id,
        "tenant_id": tenant_id,
        "site_id": site_id,
        "gateway_id": gateway_id,
        "name": name,
        "framework_id": framework_id,
        "supported_profile_ids": supported_profile_ids,
        "status": status,
        "workflow_status": None,
        "model": None,
        "error_reason": None,
    }
    
    final_state: CreateModelState = await app.ainvoke(initial_state)
    return final_state
