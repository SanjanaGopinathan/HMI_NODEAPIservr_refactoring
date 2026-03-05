# list_mcp_tools.py

import asyncio
from fastmcp import Client as FastMCPClient


MCP_SERVER_URL = "http://localhost:8001/mcp-server/mcp"


async def main():
    client = FastMCPClient(MCP_SERVER_URL)

    async with client:
        tools = await client.list_tools()

    print(f"Discovered {len(tools)} tool(s):\n")
    for t in tools:
        print(f"- {t.name}")
        if t.description:
            print(f"  desc: {t.description}")
        if t.inputSchema:
            print(f"  input schema: {t.inputSchema}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
