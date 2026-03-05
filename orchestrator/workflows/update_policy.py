from typing import TypedDict, Optional, Dict, Any, List
from langgraph.graph import StateGraph, END
from orchestrator.mcp_client import MCPClient


class UpdatePolicyState(TypedDict):
    """State for update_policy workflow"""
    # Input
    policy_id: str
    tenant_id: str
    site_id: str
    anomaly_type: Optional[str]
    severity_levels: Optional[List[str]]
    channels: Optional[List[str]]
    person_ids: Optional[List[str]]
    min_severity: Optional[str]
    enabled: Optional[bool]
    priority: Optional[int]
    
    # Output
    result: Optional[Dict]
    status: Optional[str]  # "updated", "error", "skipped"
    error_reason: Optional[str]


# --- Node implementations ---

async def node_update_policy(state: UpdatePolicyState, mcp: MCPClient) -> UpdatePolicyState:
    """Update the alert policy"""
    res = await mcp.call_tool(
        "update_policy",
        {
            "policy_id": state["policy_id"],
            "tenant_id": state["tenant_id"],
            "site_id": state["site_id"],
            "anomaly_type": state.get("anomaly_type"),
            "severity_levels": state.get("severity_levels"),
            "channels": state.get("channels"),
            "person_ids": state.get("person_ids"),
            "min_severity": state.get("min_severity"),
            "enabled": state.get("enabled"),
            "priority": state.get("priority"),
        }
    )
    
    if res.get("success"):
        state["result"] = res.get("policy")
        state["status"] = "updated"
        print(f"✅ Policy '{state['policy_id']}' updated successfully")
    elif res.get("message") and "No changes" in res.get("message"):
         state["result"] = res.get("policy")
         state["status"] = "skipped"
         print(f"ℹ️  Policy '{state['policy_id']}' update skipped: No changes")
    else:
        state["status"] = "error"
        state["error_reason"] = res.get("error", "Unknown error")
        print(f"❌ Failed to update policy '{state['policy_id']}': {state['error_reason']}")
    
    return state


# --- Graph builder ---

def build_update_policy_graph(mcp: MCPClient):
    """Build and compile the update_policy workflow"""
    builder = StateGraph(UpdatePolicyState)
    
    # Wrap nodes
    async def update_policy_node(state: UpdatePolicyState) -> UpdatePolicyState:
        return await node_update_policy(state, mcp)
    
    # Register nodes
    builder.add_node("update_policy", update_policy_node)
    
    # Entry point
    builder.set_entry_point("update_policy")
    
    # Edges
    builder.add_edge("update_policy", END)
    
    return builder.compile()


async def run_update_policy_workflow(
    mcp: MCPClient,
    policy_id: str,
    tenant_id: str,
    site_id: str,
    anomaly_type: Optional[str] = None,
    severity_levels: Optional[List[str]] = None,
    channels: Optional[List[str]] = None,
    person_ids: Optional[List[str]] = None,
    min_severity: Optional[str] = None,
    enabled: Optional[bool] = None,
    priority: Optional[int] = None,
) -> UpdatePolicyState:
    """Run the update_policy workflow"""
    app = build_update_policy_graph(mcp)
    
    initial_state: UpdatePolicyState = {
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
        "result": None,
        "status": None,
        "error_reason": None
    }
    
    final_state: UpdatePolicyState = await app.ainvoke(initial_state)
    return final_state
