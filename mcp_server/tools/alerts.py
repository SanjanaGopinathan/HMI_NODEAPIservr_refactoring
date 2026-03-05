# mcp_server/tools/alerts.py
#from fastmcp import tool
from typing import Dict, Any, List
from mcp_server.data_store import MOCK_ALERT_POLICIES
from mcp_server.server import mcp

@mcp.tool()
async def set_alert_policy(
    tenant_id: str,
    name: str,
    camera_ids: List[str],
    target_profile_ids: List[str],
    severity_levels: List[str],
    channels: List[str],
    primary_person_ids: List[str],
    escalation_person_ids: List[str] | None = None,
) -> Dict[str, Any]:
    """
    Create or update an in-memory alert policy.
    Upsert by (tenant_id, name).
    """
    escalation_person_ids = escalation_person_ids or []

    # Try to find existing policy
    existing = None
    for p in MOCK_ALERT_POLICIES:
        if p["tenant_id"] == tenant_id and p["name"] == name:
            existing = p
            break

    if existing:
        policy = existing
        policy.update(
            {
                "camera_ids": camera_ids,
                "target_profile_ids": target_profile_ids,
                "severity_levels": severity_levels,
                "channels": channels,
                "primary_person_ids": primary_person_ids,
                "escalation_person_ids": escalation_person_ids,
            }
        )
    else:
        policy = {
            "_id": f"POLICY_{len(MOCK_ALERT_POLICIES) + 1}",
            "tenant_id": tenant_id,
            "name": name,
            "camera_ids": camera_ids,
            "target_profile_ids": target_profile_ids,
            "severity_levels": severity_levels,
            "channels": channels,
            "primary_person_ids": primary_person_ids,
            "escalation_person_ids": escalation_person_ids,
        }
        MOCK_ALERT_POLICIES.append(policy)

    return {"status": "ok", "policy": policy}
