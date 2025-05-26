import asyncio
from agno.tools.mcp import MCPTools


async def test_mcptools():
    print("Testing MCPTools individual tool exposure...")

    async with MCPTools(transport="sse", url="http://localhost:8001/sse") as mcp_tools:
        print(f"MCPTools instance: {mcp_tools}")
        print(f"MCPTools type: {type(mcp_tools)}")
        print(
            f"MCPTools dir: {[attr for attr in dir(mcp_tools) if not attr.startswith('_')]}"
        )

        # Check if individual tools are exposed
        if hasattr(mcp_tools, "tools"):
            print(f"MCPTools.tools: {mcp_tools.tools}")

        if hasattr(mcp_tools, "get_tools"):
            try:
                tools = await mcp_tools.get_tools()
                print(f"Available tools via get_tools(): {tools}")
            except Exception as e:
                print(f"get_tools() error: {e}")

        # Check session
        if hasattr(mcp_tools, "session") and mcp_tools.session:
            try:
                tools_response = await mcp_tools.session.list_tools()
                tool_names = [tool.name for tool in tools_response.tools]
                print(f"Tools from session.list_tools(): {tool_names}")
            except Exception as e:
                print(f"session.list_tools() error: {e}")


if __name__ == "__main__":
    asyncio.run(test_mcptools())
