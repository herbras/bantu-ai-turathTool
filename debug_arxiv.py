try:
    from agno.tools.arxiv import ArxivTools
    
    print("🔍 Debugging ArxivTools methods")
    print("-" * 40)
    
    arxiv = ArxivTools()
    
    # Get all methods that don't start with underscore
    methods = [method for method in dir(arxiv) if not method.startswith('_')]
    
    print("📋 Available ArxivTools methods:")
    for method in methods:
        print(f"  - {method}")
    
    # Check for search-related methods specifically  
    search_methods = [method for method in methods if 'search' in method.lower()]
    print(f"\n🔍 Search-related methods: {search_methods}")
    
    # Check if it has a tools attribute (common in Agno tools)
    if hasattr(arxiv, 'tools'):
        print(f"\n🛠️ Tools attribute found: {arxiv.tools}")
        
    # Try to inspect the actual tool functions
    try:
        # Check if it's a Toolkit with tools
        if hasattr(arxiv, 'tools') and isinstance(arxiv.tools, list):
            print(f"\n📦 Tool functions:")
            for tool in arxiv.tools:
                if hasattr(tool, '__name__'):
                    print(f"  - {tool.__name__}")
                else:
                    print(f"  - {tool}")
    except Exception as e:
        print(f"Error inspecting tools: {e}")
        
except ImportError as e:
    print(f"❌ Cannot import ArxivTools: {e}")
except Exception as e:
    print(f"❌ Error: {e}") 