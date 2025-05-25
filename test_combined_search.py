import asyncio
import os
from agno.tools.mcp import MCPTools
from src.tools.tavily_service import TurathTavilyTools
from src.agents.turath_query import create_turath_query_agent

async def test_combined_search():
    print('Testing Combined MCP + Tavily Search...')
    
    # Set dummy API key for testing (replace with real key)
    os.environ["TAVILY_API_KEY"] = "your-tavily-api-key-here"
    
    async with MCPTools(transport='sse', url='http://localhost:8001/sse') as mcp_tools:
        print(f'✅ MCPTools connected with functions: {list(mcp_tools.functions.keys())}')
        
        # Initialize TavilyTools (will skip if no API key)
        try:
            tavily_tools = TurathTavilyTools()
            print(f'✅ TavilyTools initialized')
        except Exception as e:
            print(f'⚠️ TavilyTools failed (expected if no API key): {e}')
            tavily_tools = None
        
        # Create agent with both tools
        agent = create_turath_query_agent(
            mcp_tools_instance=mcp_tools,
            tavily_tools_instance=tavily_tools
        )
        await agent.initialize()
        
        tools_count = len(agent.tools)
        tool_names = [tool.name if hasattr(tool, 'name') else tool.__class__.__name__ for tool in agent.tools]
        print(f'✅ Agent created with {tools_count} tool instances: {tool_names}')
        
        # Test query
        query = "Cari buku tentang kaidah fiqh Syafi'i dan rujukan web tentang topik ini"
        print(f"Query: {query}")
        
        try:
            result = await agent.arun(query)
            print(f"\nResult: {result}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_combined_search()) 