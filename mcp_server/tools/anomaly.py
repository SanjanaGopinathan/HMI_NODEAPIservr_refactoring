import logging
from typing import List, Dict, Any
from mcp_server.server import mcp

from mcp_server.data_store import (
    MOCK_ASSETS,
    MOCK_PERSONNEL,
    MOCK_ALERT_POLICIES,
    SEVERITY_ORDER,
    severity_gte,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("mcp.route_anomaly_alert")

def _resolve_cameras_for_tenant_site(
    camera_ids: List[str],
    tenant_id: str,
    site_id: str,
) -> List[Dict[str, Any]]:
    resolved: List[Dict[str, Any]] = []
    for cam in MOCK_ASSETS:
        if (
            cam.get("_id") in camera_ids
            and cam.get("tenant_id") == tenant_id
            and cam.get("site_id") == site_id
        ):
            resolved.append(cam)
    return resolved


def _group_personnel_by_role(tenant_id: str) -> Dict[str, Dict[str, Any]]:
    """
    { role: person_doc }
    """
    by_role: Dict[str, Dict[str, Any]] = {}
    for p in MOCK_PERSONNEL:
        if p.get("tenant_id") != tenant_id:
            continue
        role = p.get("role")
        if role:
            by_role[role] = p
    return by_role


def _index_personnel_by_id(tenant_id: str) -> Dict[str, Dict[str, Any]]:
    """
    { _id: person_doc }
    """
    by_id: Dict[str, Dict[str, Any]] = {}
    for p in MOCK_PERSONNEL:
        if p.get("tenant_id") != tenant_id:
            continue
        pid = p.get("_id")
        if pid:
            by_id[pid] = p
    return by_id

@mcp.tool()
async def route_anomaly_alert(
    tenant_id: str,
    site_id: str,
    camera_ids: List[str],
    anomaly_type: str,
    severity: str,
) -> Dict[str, Any]:
    """
    Anomaly routing MCP tool using the SAME data store as PPE workflow.
    """

    logger.info("route_anomaly_alert called: tenant=%s site=%s cameras=%s anomaly=%s severity=%s",
                tenant_id, site_id, camera_ids, anomaly_type, severity)

    # 1) Resolve cameras from MOCK_CAMERAS
    resolved_cameras = _resolve_cameras_for_tenant_site(
        camera_ids=camera_ids,
        tenant_id=tenant_id,
        site_id=site_id,
    )

    if not resolved_cameras:
        logger.warning("No matching cameras for tenant/site")
        return {
            "resolved_cameras": [],
            "decisions": [],
            "status_code": 404,
            "description": "No matching cameras for tenant/site",
        }

    logger.info("Resolved cameras: %s", [c["_id"] for c in resolved_cameras])

    # 2) Resolve personnel from MOCK_PERSONNEL
    by_role = _group_personnel_by_role(tenant_id=tenant_id)
    by_id = _index_personnel_by_id(tenant_id=tenant_id)

    if not by_role and not by_id:
        logger.warning("No personnel for tenant %s", tenant_id)
        return {
            "resolved_cameras": [],
            "decisions": [],
            "status_code": 404,
            "description": f"No personnel for tenant {tenant_id}",
        }

    logger.info("Personnel roles available: %s", list(by_role.keys()))
    logger.info("Personnel ids available: %s", list(by_id.keys()))

    # 3) Find matching alert policy from MOCK_ALERT_POLICIES
    matching_policy = None
    for policy in MOCK_ALERT_POLICIES:
        if (
            policy.get("tenant_id") == tenant_id
            and policy.get("site_id") == site_id
            and policy.get("anomaly_type", "").upper() == anomaly_type.upper()
            and severity_gte(severity, policy.get("min_severity", "INFO"))
        ):
            matching_policy = policy
            break

    logger.info("Matching policy: %s", matching_policy)

    if not matching_policy:
        return {
            "resolved_cameras": [],
            "decisions": [],
            "status_code": 404,
            "description": "No alert policy for anomaly",
        }

    # 4) Pick the best route for the given severity (<= requested, but max possible)
    try:
        requested_idx = SEVERITY_ORDER.index(severity.upper())
    except ValueError:
        return {
            "resolved_cameras": [],
            "decisions": [],
            "status_code": 400,
            "description": "Unknown severity",
        }

    logger.info("requested_idx = %s", requested_idx)

    best_route = None
    best_idx = -1
    for route in matching_policy.get("routes", []):
        sev = route.get("severity", "").upper()
        if sev not in SEVERITY_ORDER:
            continue
        idx = SEVERITY_ORDER.index(sev)
        if idx <= requested_idx and idx > best_idx:
            best_route = route
            best_idx = idx

    if not best_route:
        return {
            "resolved_cameras": [],
            "decisions": [],
            "status_code": 404,
            "description": "No matching route for severity",
        }

    logger.info("Best route chosen: %s", best_route)

    # 5) Build routing decisions based on personnel and channels
    decisions: List[Dict[str, Any]] = []

    # Support both "targets" as roles OR as personnel ids
    raw_targets = best_route.get("targets", []) or []
    logger.info("Raw targets in best_route: %s", raw_targets)

    for target in raw_targets:
        # Try role first
        person = by_role.get(target)

        # If not found by role, try as personnel _id
        if not person:
            person = by_id.get(target)

        if not person:
            logger.warning("No person found for target '%s'", target)
            continue

        contact = person.get("contact", {})
        logger.info("Using person %s for target %s", person.get("_id"), target)

        for channel in best_route.get("channels", []):
            ch = channel.upper()
            if ch == "HMI_POPUP":
                address = {"type": "HMI", "target": "HMI_CONSOLE"}
            elif ch == "EMAIL":
                address = {"type": "EMAIL", "address": contact.get("email")}
            elif ch == "PHONE_CALL":
                address = {"type": "PHONE", "number": contact.get("phone")}
            else:
                address = {"type": "UNKNOWN"}

            decisions.append(
                {
                    "channel": channel,
                    "target_role": person.get("role"),
                    "target_name": person.get("name"),
                    "target_id": person.get("_id"),
                    "address": address,
                }
            )

    logger.info("Total decisions built: %d", len(decisions))

    return {
        "resolved_cameras": [
            {
                "camera_id": cam["_id"],
                "name": cam["name"],
                "location": cam["location"],
                "status": cam["status"],
                "assigned_cv_model_id": cam["assigned_cv_model_id"],
                "target_profile_ids": cam["target_profile_ids"],
                "tenant_id": cam["tenant_id"],
                "site_id": cam["site_id"],
            }
            for cam in resolved_cameras
        ],
        "decisions": decisions,
        "status_code": 200,
        "description": "OK",
    }