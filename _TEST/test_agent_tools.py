import asyncio
import logging
from agno.tools.mcp import MCPTools
from src.agents.turath_query import create_turath_query_agent

# Configure logging to only show important messages
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

async def test_agent_tools():
    print('Testing Agent with MCPTools...')
    
    async with MCPTools(transport='sse', url='http://localhost:8001/sse') as mcp_tools:
        print(f'✅ MCPTools connected with functions: {mcp_tools.functions}')
        
        # Create agent
        agent = create_turath_query_agent(mcp_tools_instance=mcp_tools)
        await agent.initialize()
        
        print(f'✅ Agent created with tools: {[tool.name if hasattr(tool, "name") else tool.__class__.__name__ for tool in agent.tools]}')
        
        # Check if agent can access individual functions
        if hasattr(agent, 'tools') and agent.tools:
            for i, tool in enumerate(agent.tools):
                print(f'Tool {i+1}: {tool.__class__.__name__}')
                if hasattr(tool, 'functions'):
                    print(f'  - Functions: {tool.functions}')
                if hasattr(tool, 'name'):
                    print(f'  - Name: {tool.name}')
                
        # Simple test without actual query to avoid long output
        print("\n=== Tool Registration Test Complete ===")
        print("MCPTools individual functions should be accessible to the agent.")

if __name__ == "__main__":
    asyncio.run(test_agent_tools()) 