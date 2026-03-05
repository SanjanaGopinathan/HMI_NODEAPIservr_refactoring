# ai_agent/anomaly_agent.py

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from openai import OpenAI

from orchestrator_client import route_anomaly_alert_workflow


client = OpenAI()

SYSTEM_PROMPT = """
You are an Anomaly Escalation Agent for an industrial safety system.

You receive:
- An anomaly event (camera_ids, anomaly_type, severity, etc.)
- Suggested alert routes from the Orchestrator (routes, policies, personnel)

Your job:
- Decide WHO should be notified and via WHICH channels.
- Optionally escalate beyond the suggested routes if severity or context demands it.
- Always produce:
  - A structured escalation plan (list of actions)
  - A natural-language explanation of why you chose this plan.

You MUST:
- Respect tenant_id and site_id.
- Treat severity=CRITICAL as high priority.
- Prefer alerting Safety Officer first, then Supervisor, then Plant Manager (if present).
"""


def build_llm_messages(
    anomaly_event: Dict[str, Any],
    routing_result: Dict[str, Any],
) -> list[Dict[str, str]]:
    """
    Build messages for GPT:
      - system prompt
      - user message with anomaly + routing result
    """
    user_content = (
        "Here is a new anomaly event and the orchestrator's suggested routes.\n\n"
        f"Anomaly Event:\n{json.dumps(anomaly_event, indent=2)}\n\n"
        f"Routing Result:\n{json.dumps(routing_result, indent=2)}\n\n"
        "Please decide final escalation steps. "
        "Return a short JSON plan plus a human-readable explanation."
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def call_llm_for_escalation(
    anomaly_event: Dict[str, Any],
    routing_result: Dict[str, Any],
    model: str = "gpt-4.1-mini",
) -> Dict[str, Any]:
    """
    Call OpenAI to generate the final escalation plan.

    Returns a dict like:
    {
      "plan": { ... },          # machine-readable
      "explanation": "..."      # human-friendly
    }
    """
    messages = build_llm_messages(anomaly_event, routing_result)

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
    )

    msg = resp.choices[0].message
    text = msg.content

    # Simple parsing heuristic:
    # Ask model to respond with a JSON block first and explanation after.
    # For a skeleton, we just wrap raw text.
    return {
        "raw_response": text,
        # You can later refine this to force a JSON-only first message.
    }


def send_notifications_stub(plan_result: Dict[str, Any]) -> None:
    """
    Stub function for sending notifications.

    In a real system, this would:
      - Call SMS gateways
      - Send emails
      - Trigger SIP/MCPTT/PTT calls
      - Push events to Teams/Slack, etc.

    For now, we simply log/print.
    """
    print("[notify] (stub) Would send notifications based on:")
    print(json.dumps(plan_result, indent=2))


def handle_anomaly_event(anomaly_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point used by the Agent API.

    Steps:
      1. Call orchestrator anomaly routing workflow
      2. Call LLM to decide final escalation plan
      3. Trigger notifications (stub)
      4. Return a summary back to caller (HMI)
    """
    tenant_id = anomaly_event["tenant_id"]
    site_id = anomaly_event["site_id"]
    camera_ids = anomaly_event["camera_ids"]
    anomaly_type = anomaly_event["anomaly_type"]
    severity = anomaly_event.get("severity", "WARN")

    # 1. Ask orchestrator for base routes
    routing_result = route_anomaly_alert_workflow(
        tenant_id=tenant_id,
        site_id=site_id,
        camera_ids=camera_ids,
        anomaly_type=anomaly_type,
        severity=severity,
    )

    # 2. Ask LLM to refine/decide escalation
    escalation_decision = call_llm_for_escalation(
        anomaly_event=anomaly_event,
        routing_result=routing_result,
    )

    # 3. Trigger notifications (stub for now)
    send_notifications_stub(escalation_decision)

    # 4. Build response to HMI
    return {
        "anomaly_event": anomaly_event,
        "routing_result": routing_result,
        "escalation_decision": escalation_decision,
    }
