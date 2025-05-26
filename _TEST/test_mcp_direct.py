import asyncio
from agno.tools.mcp import MCPTools

async def test_mcp_direct():
    print('Testing direct MCP function calls...')
    
    async with MCPTools(transport='sse', url='http://localhost:8001/sse') as mcp_tools:
        print(f'✅ MCPTools connected')
        print(f'Available functions: {list(mcp_tools.functions.keys())}')
        
        # Test list_all_categories first to see what's available
        print("\n=== Testing list_all_categories ===")
        try:
            result = await mcp_tools.session.call_tool('list_all_categories', {})
            print(f"Categories result: {result}")
            
            if hasattr(result, 'content') and result.content:
                for content_item in result.content:
                    if hasattr(content_item, 'text'):
                        print(f"Categories: {content_item.text}")
                        
        except Exception as e:
            print(f"❌ Error calling list_all_categories: {e}")
        
        # Test get_filter_ids with different terms
        print("\n=== Testing get_filter_ids with different terms ===")
        test_terms = ['فقه', 'الفقه', 'فقه الشافعي', 'نحو']
        
        for term in test_terms:
            try:
                result = await mcp_tools.session.call_tool(
                    'get_filter_ids', 
                    {'category_name': term}
                )
                print(f"Term '{term}': {result}")
                
                if hasattr(result, 'content') and result.content:
                    for content_item in result.content:
                        if hasattr(content_item, 'text'):
                            print(f"  Content: {content_item.text}")
                            
            except Exception as e:
                print(f"❌ Error with term '{term}': {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_direct()) 