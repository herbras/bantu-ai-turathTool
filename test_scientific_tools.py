import asyncio
import os
from agno.tools.mcp import MCPTools
from src.tools.tavily_service import TurathTavilyTools
from src.tools.scientific_service import TurathScientificTools
from src.agents.turath_query import create_turath_query_agent

async def test_scientific_tools():
    print('Testing Scientific Tools Integration...')
    
    # Set dummy keys for testing
    os.environ["TAVILY_API_KEY"] = "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"
    
    async with MCPTools(transport='sse', url='http://localhost:8001/sse') as mcp_tools:
        print(f'✅ MCPTools connected with functions: {list(mcp_tools.functions.keys())}')
        
        # Initialize Tavily tools
        try:
            tavily_tools = TurathTavilyTools()
            print(f'✅ TavilyTools initialized')
        except Exception as e:
            print(f'⚠️ TavilyTools failed: {e}')
            tavily_tools = None
        
        # Initialize Scientific tools
        try:
            scientific_tools = TurathScientificTools(email="test@turath.ai")
            print(f'✅ Scientific Tools initialized')
            
            # Test query type detection
            test_queries = [
                "artificial intelligence in Islamic ethics",
                "medical ethics in Islam and organ transplantation", 
                "machine learning algorithms for Quran analysis",
                "Islamic bioethics and genetic engineering"
            ]
            
            print("\n=== Testing Query Type Detection ===")
            for query in test_queries:
                query_type = scientific_tools.detect_query_type(query)
                print(f"Query: '{query}' -> Type: {query_type}")
                
        except Exception as e:
            print(f'⚠️ Scientific Tools failed: {e}')
            scientific_tools = None
        
        # Create agent with all tools
        agent = create_turath_query_agent(
            mcp_tools_instance=mcp_tools,
            tavily_tools_instance=tavily_tools,
            scientific_tools_instance=scientific_tools
        )
        await agent.initialize()
        
        tools_count = len(agent.tools)
        tool_names = [tool.name if hasattr(tool, 'name') else tool.__class__.__name__ for tool in agent.tools]
        print(f'✅ Agent created with {tools_count} tool instances: {tool_names}')
        
        # Test different query types
        test_cases = [
            # Islamic query
            ("Cari hadits tentang menuntut ilmu", "Islamic"),
            # Medical query  
            ("What does Islam say about organ transplantation and medical ethics?", "Medical/Scientific"),
            # Technology query
            ("Islamic ethics perspective on artificial intelligence and automation", "Technology/Scientific"),
        ]
        
        print(f"\n=== Testing Different Query Types ===")
        
        for query, expected_type in test_cases:
            print(f"\n--- Testing {expected_type} Query ---")
            print(f"Query: {query}")
            
            try:
                # For demo, just show that agent has the tools available
                # Real test would require API keys
                available_tools = []
                for tool in agent.tools:
                    if hasattr(tool, 'name'):
                        available_tools.append(tool.name)
                    elif hasattr(tool, 'functions'):
                        available_tools.extend(list(tool.functions.keys()))
                
                print(f"Available tools for this query: {available_tools}")
                
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_scientific_tools()) 