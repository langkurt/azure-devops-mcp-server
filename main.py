"""
Azure DevOps MCP Server for Ticket Management

This MCP server implements functionality to create and update tickets (work items) 
in Azure DevOps through a standardized Model Context Protocol interface.
"""

from mcp.server.fastmcp import FastMCP

# Import tools
from tools.create_work_item import create_work_item
from tools.update_work_item import update_work_item
from tools.add_work_item_comment import add_work_item_comment
from tools.get_work_item import get_work_item
from tools.get_my_sprint_work_items import get_my_sprint_work_items
from tools.search_work_items import search_work_items

# Initialize MCP server
mcp = FastMCP(
    "Azure DevOps Ticket Manager",
    description="Create and update tickets (work items) in Azure DevOps"
)

# Register tools
mcp.tool()(create_work_item)
mcp.tool()(update_work_item)
mcp.tool()(add_work_item_comment)
mcp.tool()(get_work_item)
mcp.tool()(get_my_sprint_work_items)
mcp.tool()(search_work_items)

if __name__ == "__main__":
    # Run the MCP server with stdio transport
    print("Starting Azure DevOps MCP Server...")
    mcp.run()