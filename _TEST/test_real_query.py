import asyncio
import logging
from agno.tools.mcp import MCPTools
from src.agents.turath_query import create_turath_query_agent

# Configure logging to see tool calls
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

async def test_real_query():
    print('Testing real query with MCPTools...')
    
    async with MCPTools(transport='sse', url='http://localhost:8001/sse') as mcp_tools:
        print(f'✅ MCPTools connected with functions: {list(mcp_tools.functions.keys())}')
        
        # Create agent
        agent = create_turath_query_agent(mcp_tools_instance=mcp_tools)
        await agent.initialize()
        
        print(f'✅ Agent tools: {[tool.name if hasattr(tool, "name") else tool.__class__.__name__ for tool in agent.tools]}')
        
        # Test with a simple Indonesian query that should trigger get_filter_ids
        print("\n=== Testing with real query ===")
        query = "Cari ID kategori untuk 'fiqih'"
        
        try:
            print(f"Query: {query}")
            result = await agent.arun(query)
            print(f"\n✅ Result: {result}")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_query()) 