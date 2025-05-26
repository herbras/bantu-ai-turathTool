import asyncio
from agno.tools.mcp import MCPTools
from src.agents.turath_query import create_turath_query_agent

async def test_agent_simple():
    print('Testing if agent uses MCP tools...')
    
    async with MCPTools(transport='sse', url='http://localhost:8001/sse') as mcp_tools:
        # Create agent
        agent = create_turath_query_agent(mcp_tools_instance=mcp_tools)
        agent.show_tool_calls = True
        await agent.initialize()
        
        print(f'Agent created with {len(agent.tools)} tools')
        
        # Test query
        query = "List all categories"
        print(f"Query: {query}")
        
        try:
            result = await agent.arun(query)
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent_simple()) 