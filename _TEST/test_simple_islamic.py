import asyncio
from agno.tools.mcp import MCPTools
from src.agents.turath_query import create_turath_query_agent

async def test_simple_islamic():
    print('Testing simple Islamic query...')
    
    async with MCPTools(transport='sse', url='http://localhost:8001/sse') as mcp_tools:
        agent = create_turath_query_agent(mcp_tools_instance=mcp_tools)
        await agent.initialize()
        
        # Simple query that should use get_filter_ids and search_library
        query = "Cari buku tentang الفقه الشافعي"
        print(f"Query: {query}")
        
        try:
            result = await agent.arun(query)
            print(f"\nResult: {result}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_islamic()) 