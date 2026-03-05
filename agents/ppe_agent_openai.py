# ppe_agent_openai.py

"""
Simple OpenAI-powered PPE agent that:
- Understands a natural language request
- Uses the configure_ppe_workflow tool
- Calls your local Orchestrator
- Returns a natural language summary of what was done
"""

from __future__ import annotations

import json
import os

from openai import OpenAI

from tools_openai import configure_ppe_tool
from orchestrator_client import configure_ppe_workflow


# Make sure OPENAI_API_KEY is set in your environment
# e.g. export OPENAI_API_KEY="sk-..."
client = OpenAI()


SYSTEM_PROMPT = """
You are a PPE safety orchestration assistant.

You have access to a function called `configure_ppe_workflow` that enables PPE
monitoring for a given tenant, site, and location by calling an AI Orchestrator.

When the user asks you to enable PPE monitoring (e.g. "Enable PPE monitoring at Gate 3"),
you MUST:

1. Decide the appropriate tenant_id, site_id, and location_filter from the user text.
2. Call the `configure_ppe_workflow` tool with those parameters.
3. After tool execution, summarize the result in clear language, including:
   - How many cameras were configured
   - What profile/model/policy was applied
   - Who gets alerts (if available from the result)
"""


def main():
    # Example natural language request
    user_message = (
        "Enable PPE monitoring for Gate 3 at Site SITE_01 for tenant TENANT_01."
    )

    # 1. First call: let the model decide whether to call the tool
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        tools=[configure_ppe_tool],
        tool_choice="auto",
    )

    message = response.choices[0].message

    if not message.tool_calls:
        # Model decided not to use the tool – just print what it said
        print("Model response (no tool call):")
        print(message.content)
        return

    # We expect exactly one tool call in this simple scenario
    tool_call = message.tool_calls[0]
    tool_name = tool_call.function.name
    raw_args = tool_call.function.arguments  # JSON string

    try:
        params = json.loads(raw_args)
    except json.JSONDecodeError:
        print("Failed to decode tool arguments:", raw_args)
        return

    print(f"Tool call requested by model: {tool_name}({params})")

    # 2. Execute the tool locally (call your orchestrator)
    if tool_name == "configure_ppe_workflow":
        result = configure_ppe_workflow(
            tenant_id=params["tenant_id"],
            site_id=params["site_id"],
            location_filter=params["location_filter"],
        )
    else:
        result = {"error": f"Unknown tool {tool_name}"}

    print("\nRaw orchestrator result:")
    print(json.dumps(result, indent=2))

    # 3. Send the tool result back to the model so it can summarize nicely
    followup = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
            message,  # original assistant message that contained the tool call
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": json.dumps(result),
            },
        ],
    )

    final_message = followup.choices[0].message
    print("\nNatural language summary from model:")
    print(final_message.content)


if __name__ == "__main__":
    main()
