import asyncio
from fastmcp import Client, FastMCP

from server import mcp

# Local Python script
client = Client(mcp)

async def main():
    async with client:
        # Basic server interaction
        await client.ping()

        # List available operations
        tools = await client.list_tools()
        resources = await client.list_resources()
        
        print("\n=== Tools Available to LLM ===")
        for tool in tools:
            print(f"Name: {tool.name}")
            print(f"Description: {tool.description}")
            print(f"Schema: {tool.inputSchema}")
            print("-" * 20)

        print("\n=== Resources Available to LLM ===")
        for resource in resources:
            print(f"URI: {resource.uri}")
            print(f"Name: {resource.name}")
            print(f"Description: {resource.description}")
            print("-" * 20)

asyncio.run(main())