from agno.tools.arxiv import ArxivTools
import inspect

try:
    arxiv = ArxivTools()
    
    # Get method signature
    method = getattr(arxiv, 'search_arxiv_and_return_articles')
    signature = inspect.signature(method)
    
    print(f"🔍 Method signature: {signature}")
    print(f"📋 Parameters:")
    
    for param_name, param in signature.parameters.items():
        print(f"  - {param_name}: {param}")
        
    # Also check docstring if available
    if method.__doc__:
        print(f"\n📝 Docstring:\n{method.__doc__}")
    else:
        print("\n📝 No docstring available")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 