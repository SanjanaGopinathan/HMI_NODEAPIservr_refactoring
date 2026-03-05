from typing import TypedDict, List, Optional, Dict, Any, Literal

from langgraph.graph import StateGraph, END
from orchestrator.mcp_client import MCPClient


class AnomalyState(TypedDict, total=False):
    tenant_id: str
    site_id: str
    camera_ids: List[str]
    anomaly_type: str
    severity: str

    validated: bool
    mcp_result: Dict[str, Any]
    error: Optional[str]


async def validate_alert_node(state: AnomalyState) -> AnomalyState:
    try:
        required = ["tenant_id", "site_id", "camera_ids", "anomaly_type", "severity"]
        for key in required:
            if key not in state or not state[key]:
                raise ValueError(f"Missing field: {key}")
        if not isinstance(state["camera_ids"], list) or not state["camera_ids"]:
            raise ValueError("camera_ids must be non-empty list")
        state["validated"] = True
        state["error"] = None
    except Exception as e:
        state["validated"] = False
        state["error"] = str(e)
    return state


async def node_lookup_policy(state: AnomalyState, mcp: MCPClient) -> AnomalyState:
    if not state.get("validated"):
        return state

    try:
        args = {
            "tenant_id": state["tenant_id"],
            "site_id": state["site_id"],
            "camera_ids": state["camera_ids"],
            "anomaly_type": state["anomaly_type"],
            "severity": state["severity"],
        }
        result = await mcp.call_tool("route_anomaly_alert", args)
        state["mcp_result"] = result
        state["error"] = None
    except Exception as e:
        state["error"] = f"MCP error: {e}"
    return state

async def finalize_node(state: AnomalyState) -> AnomalyState:
    # For now, this node just passes state through.
    return state

# --- Graph builder ---

def build_route_anomaly_alert_graph(mcp: MCPClient):
    """
    Build and compile the LangGraph workflow for 'Enable PPE monitoring'.
    Returns a compiled app that supports .invoke() / .ainvoke().
    """
    builder = StateGraph(AnomalyState)

    # Wrap each node_* function in an async closure that binds mcp
    async def lookup_policy_node(state: AnomalyState) -> AnomalyState:
        return await node_lookup_policy(state, mcp)

    builder.add_node("validate_alert", validate_alert_node)
    builder.add_node("lookup_policy", lookup_policy_node)
    builder.add_node("finalize", finalize_node)

    builder.set_entry_point("validate_alert")
    builder.add_edge("validate_alert", "lookup_policy")
    builder.add_edge("lookup_policy", "finalize")
    builder.add_edge("finalize", END)

    # Compile to a runnable app
    app = builder.compile()
    return app


async def run_route_anomaly_alert_workflow(
    mcp: MCPClient,
    tenant_id: str,
    site_id: str,
    camera_ids: List[str],
    anomaly_type: str,
    severity: str
) -> AnomalyState:
    """
    Run the compiled Configure PPE workflow and return final state.
    """
    app = build_route_anomaly_alert_graph(mcp)

    initial_state: AnomalyState = {
        "tenant_id": tenant_id,
        "site_id": site_id,
        "camera_ids": camera_ids,
        "anomaly_type": anomaly_type,
        "severity": severity
    }

    # For async support in LangGraph
    final_state: AnomalyState = await app.ainvoke(initial_state)
    return final_state