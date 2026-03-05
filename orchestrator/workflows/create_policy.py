from typing import TypedDict, Optional, Dict, Any, List
from langgraph.graph import StateGraph, END
from orchestrator.mcp_client import MCPClient


class CreatePolicyState(TypedDict):
    """State for create_policy workflow"""
    # Input
    policy_id: str
    tenant_id: str
    site_id: str
    anomaly_type: str
    severity_levels: List[str]
    channels: List[str]
    person_ids: List[str]
    min_severity: Optional[str]
    enabled: Optional[bool]
    priority: Optional[int]
    
    # Output
    policy: Optional[Dict]
    status: Optional[str]  # "exists", "created", "error"
    error_reason: Optional[str]


# --- Node implementations ---

async def node_check_policy_exists(state: CreatePolicyState, mcp: MCPClient) -> CreatePolicyState:
    """Check if policy already exists"""
    res = await mcp.call_tool(
        "list_policy",
        {
            "tenant_id": state["tenant_id"],
            "site_id": state["site_id"],
            "anomaly_type": state["anomaly_type"],
        }
    )
    
    policies = res.get("policies", [])
    # Check by ID or by anomaly_type
    existing = next(
        (p for p in policies if p.get("_id") == state["policy_id"]),
        None
    )
    
    if existing:
        state["status"] = "exists"
        state["policy"] = existing
        print(f"ℹ️  Policy '{state['policy_id']}' already exists")
    else:
        state["status"] = "create"
    
    return state


async def node_create_policy(state: CreatePolicyState, mcp: MCPClient) -> CreatePolicyState:
    """Create the alert policy"""
    res = await mcp.call_tool(
        "create_policy",
        {
            "policy_id": state["policy_id"],
            "tenant_id": state["tenant_id"],
            "site_id": state["site_id"],
            "anomaly_type": state["anomaly_type"],
            "severity_levels": state["severity_levels"],
            "channels": state["channels"],
            "person_ids": state["person_ids"],
            "min_severity": state.get("min_severity", "WARNING"),
            "enabled": state.get("enabled", True),
            "priority": state.get("priority", 100),
        }
    )
    
    if res.get("success"):
        state["policy"] = res.get("policy")
        state["status"] = "created"
        print(f"✅ Policy '{state['policy_id']}' created successfully")
    else:
        state["status"] = "error"
        state["error_reason"] = res.get("error", "Unknown error")
        print(f"❌ Failed to create policy '{state['policy_id']}': {state['error_reason']}")
    
    return state


# --- Graph builder ---

def build_create_policy_graph(mcp: MCPClient):
    """Build and compile the create_policy workflow"""
    builder = StateGraph(CreatePolicyState)
    
    # Wrap nodes
    async def check_policy_exists_node(state: CreatePolicyState) -> CreatePolicyState:
        return await node_check_policy_exists(state, mcp)
    
    async def create_policy_node(state: CreatePolicyState) -> CreatePolicyState:
        return await node_create_policy(state, mcp)
    
    # Register nodes
    builder.add_node("check_policy_exists", check_policy_exists_node)
    builder.add_node("create_policy", create_policy_node)
    
    # Entry point
    builder.set_entry_point("check_policy_exists")
    
    # Conditional transitions
    def after_check_exists(state: CreatePolicyState) -> str:
        if state.get("status") == "exists":
            return END
        return "create_policy"
    
    builder.add_conditional_edges("check_policy_exists", after_check_exists)
    builder.add_edge("create_policy", END)
    
    return builder.compile()


async def run_create_policy_workflow(
    mcp: MCPClient,
    policy_id: str,
    tenant_id: str,
    site_id: str,
    anomaly_type: str,
    severity_levels: List[str],
    channels: List[str],
    person_ids: List[str],
    min_severity: Optional[str] = None,
    enabled: Optional[bool] = None,
    priority: Optional[int] = None,
) -> CreatePolicyState:
    """Run the create_policy workflow"""
    app = build_create_policy_graph(mcp)
    
    initial_state: CreatePolicyState = {
        "policy_id": policy_id,
        "tenant_id": tenant_id,
        "site_id": site_id,
        "anomaly_type": anomaly_type,
        "severity_levels": severity_levels,
        "channels": channels,
        "person_ids": person_ids,
        "min_severity": min_severity,
        "enabled": enabled,
        "priority": priority,
    }
    
    final_state: CreatePolicyState = await app.ainvoke(initial_state)
    return final_state
