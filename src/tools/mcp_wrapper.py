"""
MCP Tools Wrapper that properly exposes individual MCP functions as separate tools
"""
import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable
from agno.tools.mcp import MCPTools

logger = logging.getLogger(__name__)


async def create_individual_mcp_tools(mcp_tools: MCPTools) -> List[Callable]:
    """Create individual tool functions from MCP server tools"""
    individual_tools = []
    
    try:
        # Get the MCP session and list available tools
        if hasattr(mcp_tools, 'session') and mcp_tools.session:
            # List tools from MCP server
            tools_response = await mcp_tools.session.list_tools()
            logger.info(f"Available MCP tools: {[tool.name for tool in tools_response.tools]}")
            
            # Create individual tool functions
            for tool in tools_response.tools:
                tool_func = create_mcp_tool_function(mcp_tools, tool)
                individual_tools.append(tool_func)
                logger.info(f"Registered MCP tool: {tool.name}")
                
            logger.info(f"Successfully initialized {len(individual_tools)} MCP tools")
        else:
            logger.error("MCPTools session not available")
    except Exception as e:
        logger.error(f"Failed to create individual MCP tools: {e}")
    
    return individual_tools


def create_mcp_tool_function(mcp_tools: MCPTools, tool) -> Callable:
    """Create a single tool function for an MCP tool"""
    tool_name = tool.name
    tool_description = tool.description
    
    async def mcp_tool_function(*args, **kwargs):
        """Individual MCP tool function"""
        try:
            # Prepare arguments for MCP tool call
            arguments = {}
            if args:
                # If positional args, try to map them to the tool's input schema
                if hasattr(tool, 'inputSchema') and tool.inputSchema:
                    properties = tool.inputSchema.get('properties', {})
                    property_names = list(properties.keys())
                    for i, arg in enumerate(args):
                        if i < len(property_names):
                            arguments[property_names[i]] = arg
            
            # Only add keyword arguments that are expected by the tool
            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                expected_params = tool.inputSchema.get('properties', {}).keys()
                for key, value in kwargs.items():
                    if key in expected_params:
                        arguments[key] = value
                    else:
                        logger.warning(f"Ignoring unexpected parameter '{key}' for tool {tool_name}")
            else:
                # If no schema, add all kwargs (fallback)
                arguments.update(kwargs)
            
            logger.info(f"Calling MCP tool {tool_name} with arguments: {arguments}")
            
            # Call the MCP tool via the session
            result = await mcp_tools.session.call_tool(tool_name, arguments)
            
            logger.info(f"MCP tool {tool_name} returned: {result}")
            
            # Return the content from the tool result
            if result and hasattr(result, 'content'):
                return result.content
            return result
            
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            raise
    
    # Set function metadata
    mcp_tool_function.__name__ = tool_name
    mcp_tool_function.__doc__ = tool_description
    
    return mcp_tool_function


# For backward compatibility, keep the toolkit approach as well
class TurathMCPToolkit:
    """Custom MCP Toolkit that exposes individual Turath MCP tools"""
    
    def __init__(self, mcp_tools: MCPTools):
        self.name = "TurathMCPToolkit"
        self.mcp_tools = mcp_tools
        self._tools_initialized = False
        self.individual_tools = []
        
    async def initialize_tools(self):
        """Initialize and expose individual MCP tools"""
        if self._tools_initialized:
            return
            
        self.individual_tools = await create_individual_mcp_tools(self.mcp_tools)
        self._tools_initialized = True


async def create_turath_mcp_toolkit(mcp_tools: MCPTools) -> TurathMCPToolkit:
    """Create and initialize the Turath MCP Toolkit"""
    toolkit = TurathMCPToolkit(mcp_tools)
    await toolkit.initialize_tools()
    return toolkit 