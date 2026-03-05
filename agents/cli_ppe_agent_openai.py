# cli_ppe_agent_openai.py

from __future__ import annotations

import json
import os
import sys
from typing import Dict, Any, List

from openai import OpenAI

from tools_openai import ALL_TOOLS
from orchestrator_client import (
    configure_ppe_workflow,
    route_anomaly_alert_workflow,
    create_camera_workflow,
    delete_camera_workflow,
    create_profile_workflow,
    create_policy_workflow,
    create_personnel_workflow,
    setup_ppe_site_workflow,
    setup_ppe_site_workflow,
    disable_ppe,
    query_camera_full_context,
    query_site_health,
    query_ppe_configuration_status,
    query_sticky_defaults,
)


# OpenAI client – uses OPENAI_API_KEY from env by default
client = OpenAI()


SYSTEM_PROMPT_PPE = """
You are a PPE safety orchestration assistant for an industrial site.

You have access to the following tools:
1. `configure_ppe_workflow` - Enable PPE monitoring for existing cameras
2. `create_camera_workflow` - Create a new camera asset
3. `delete_camera_workflow` - Delete a camera asset by ID
4. `create_profile_workflow` - Create a detection profile
5. `create_policy_workflow` - Create an alert policy
6. `create_personnel_workflow` - Create a new personnel record
7. `setup_ppe_site_workflow` - Complete site setup (creates cameras, profiles, policies)
8. `disable_ppe` - Disable PPE monitoring for a specific camera
9. `query_camera_full_context` - Get complete details for a camera (model, policy, profiles, personnel)
10. `query_site_health` - Analyze site configuration health and get recommendations
11. `query_ppe_configuration_status` - Check which cameras are properly configured for PPE
12. `query_sticky_defaults` - Check current tenant/site/gateway context

Rules:
- **Query Tools**: Use these to answer questions about the system state.
  * `query_site_health`: Use when user asks "is the site healthy?" or "what's wrong?".
  * `query_ppe_configuration_status`: Use when user asks "which cameras have PPE enabled?" or "who is missing PPE config?".
  * `query_camera_full_context`: Use for deep-dives on a specific camera ("tell me about camera X").
  * `query_sticky_defaults`: Use to verify what tenant/site you are working on.

- **configure_ppe_workflow**: Enable PPE monitoring for cameras. Flexible filtering:
  * Can use `camera_id` to target a specific camera (e.g., "CAM_GW_SITE_01_01")
  * Can use `location_filter` to target all cameras at a location (e.g., "Entry Gate")
  * Can use BOTH for additional filtering
  * At least ONE must be provided
- **create_camera_workflow**: Use when user wants to create a NEW camera
- **delete_camera_workflow**: Use when user wants to delete a camera by its ID
- **disable_ppe**: Use when user wants to disable PPE monitoring for a camera (sets status to INACTIVE)
- **create_profile_workflow**: Use when creating a new detection profile
- **create_policy_workflow**: Use when creating a new alert policy
- **create_personnel_workflow**: Use when creating a new personnel record
- **setup_ppe_site_workflow**: Use for complete site setup (creates cameras, profiles, policies)

- **IMPORTANT**: The orchestrator has "sticky defaults" - it remembers the last tenant_id, site_id, 
  and gateway_id you used. If the user doesn't specify these IDs:
  * DO NOT include them in your tool calls
  * The orchestrator will automatically use the last values you provided
  * This allows seamless multi-step workflows without repeating IDs
- Only include tenant_id, site_id, or gateway_id in your tool calls when:
  * The user explicitly specifies them
  * You're starting a new workflow for a different tenant/site/gateway
  * The user asks to switch context (e.g., "now work on Site 02")
  
- **ID Handling**:
  * Use IDs EXACTLY as the user provides them - do NOT modify or add suffixes
  * If user says "camera ID CAM_GW_SITE_01_01", use exactly "CAM_GW_SITE_01_01"
  * Do NOT append additional numbers or modify the format
  * The user knows the correct ID format for their system
  * Camera IDs are NOT the same as gateway IDs - don't confuse them!

After tool execution, you MUST:
- Summarize the result clearly
- Mention what was created vs what already existed (for idempotent operations)
- If there is an error, explain it and suggest next steps
"""

SYSTEM_PROMPT_ANOMALY = """
You are an Anomaly Escalation assistant.

You receive:
- An anomaly event (tenant, site, cameras, anomaly_type, severity, etc.)
- A routing result from the Orchestrator (routes, policies, personnel)

Your job:
- Summarize who will be notified and via which channels.
- Explain briefly why this routing makes sense.
- If there are no routes, explain that and suggest what needs to be configured.
"""


# ---------------------------------------------------------------------------
# Utility for parsing "/anomaly" CLI arguments
# ---------------------------------------------------------------------------

def parse_kv_args(s: str) -> Dict[str, str]:
    """
    Parse a simple "KEY=VALUE" string into a dict.
    Example:
      "camera_ids=CAM1,CAM2 anomaly_type=PPE_VIOLATION severity=CRITICAL"
    ->
      {
        "camera_ids": "CAM1,CAM2",
        "anomaly_type": "PPE_VIOLATION",
        "severity": "CRITICAL",
      }
    """
    result: Dict[str, str] = {}
    tokens = s.split()
    for tok in tokens:
        if "=" not in tok:
            continue
        key, value = tok.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key:
            result[key] = value
    return result


# ---------------------------------------------------------------------------
# PPE configuration path (existing behavior)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Core Agent Logic (Multi-turn with History & Tool Loop)
# ---------------------------------------------------------------------------

def execute_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a specific tool and return the result."""
    try:
        if tool_name == "configure_ppe_workflow":
            return configure_ppe_workflow(**params)
        elif tool_name == "create_camera_workflow":
            return create_camera_workflow(**params)
        elif tool_name == "delete_camera_workflow":
            return delete_camera_workflow(**params)
        elif tool_name == "disable_ppe":
            return disable_ppe(**params)
        elif tool_name == "create_profile_workflow":
            return create_profile_workflow(**params)
        elif tool_name == "create_policy_workflow":
            return create_policy_workflow(**params)
        elif tool_name == "create_personnel_workflow":
            return create_personnel_workflow(**params)
        elif tool_name == "setup_ppe_site_workflow":
            return setup_ppe_site_workflow(**params)
        elif tool_name == "query_camera_full_context":
            return query_camera_full_context(**params)
        elif tool_name == "query_site_health":
            return query_site_health(**params)
        elif tool_name == "query_ppe_configuration_status":
            return query_ppe_configuration_status(**params)
        elif tool_name == "query_sticky_defaults":
            return query_sticky_defaults(**params)
        else:
            return {"status": "error", "error_reason": f"Unknown tool: {tool_name}"}
    except Exception as e:
        print(f"[error] Tool execution failed: {e}")
        return {"status": "error", "error_reason": str(e)}


def call_openai_with_history(messages: List[Dict[str, Any]]):
    """Call OpenAI with the full message history."""
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        tools=ALL_TOOLS,
        tool_choice="auto",
    )
    return response.choices[0].message


def handle_ppe_conversation(messages: List[Dict[str, Any]]) -> None:
    """
    Handle the conversation loop for a user turn.
    Loops while the model keeps calling tools (ReAct pattern).
    """
    MAX_TOOL_TURNS = 5
    turn_count = 0
    
    while turn_count < MAX_TOOL_TURNS:
        try:
            assistant_msg = call_openai_with_history(messages)
        except Exception as e:
            print(f"[error] Model call failed: {e}")
            break
            
        messages.append(assistant_msg) # Add assistant's response/thought/call to history

        # Case 1: Model wants to call a tool
        if assistant_msg.tool_calls:
            tool_call = assistant_msg.tool_calls[0]
            tool_name = tool_call.function.name
            raw_args = tool_call.function.arguments
            
            try:
                params = json.loads(raw_args)
            except json.JSONDecodeError:
                print(f"[error] Failed to parse tool args: {raw_args}")
                break
                
            print(f"[tool] {tool_name} called with {params}")
            
            # Execute tool
            tool_result = execute_tool(tool_name, params)
            
            # Add tool result to history
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps(tool_result)
            })
            
            turn_count += 1
            # Loop continues -> Model sees tool result and decides next step
            
        # Case 2: Model produced a final answer (text content)
        elif assistant_msg.content:
            print("assistant>", assistant_msg.content)
            break
            
        else:
            print("[warn] Model returned empty message without tool calls.")
            break


# ---------------------------------------------------------------------------
# Main CLI loop
# ---------------------------------------------------------------------------

def run_cli():
    print("🔧 PPE Orchestrator CLI Agent (OpenAI-powered)")
    print("Commands:")
    print("  - Natural language for PPE config, e.g.:")
    print("      Enable PPE monitoring at Gate 3")
    print("  - Anomaly routing tester, e.g.:")
    print("      /anomaly camera_ids=CAM_GATE3_001 anomaly_type=PPE_VIOLATION severity=CRITICAL")
    print("Type 'exit' or 'quit' to leave.\n")

    # Initialize conversion history with System Prompt
    conversation_history = [
        {"role": "system", "content": SYSTEM_PROMPT_PPE}
    ]

    while True:
        try:
            user_message = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

        if not user_message:
            continue
        if user_message.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        if user_message.lower().startswith("/anomaly"):
            # Anomaly routing test path (Stateless)
            handle_anomaly_cli(user_message)
        else:
            # PPE/Query conversation path (Stateful)
            conversation_history.append({"role": "user", "content": user_message})
            handle_ppe_conversation(conversation_history)


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print(
            "ERROR: OPENAI_API_KEY is not set.\n"
            "Set it in your environment, e.g.:\n"
            "  $env:OPENAI_API_KEY=\"sk-...\"  (PowerShell)\n"
            "  set OPENAI_API_KEY=sk-...       (CMD)\n"
        )
        sys.exit(1)

    run_cli()
