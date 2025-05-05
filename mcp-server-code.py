"""
Azure DevOps MCP Server for Ticket Management

This MCP server implements functionality to create and update tickets (work items) 
in Azure DevOps through a standardized Model Context Protocol interface.
"""

import os
from typing import Dict, Optional, Any

from azure.devops.connection import Connection
from azure.devops.v7_1.work_item_tracking.models import JsonPatchOperation
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from msrest.authentication import BasicAuthentication

# Load environment variables from .env file
load_dotenv()

# Get Azure DevOps configuration from environment variables
AZURE_DEVOPS_PAT = os.getenv("AZURE_DEVOPS_PAT")
AZURE_DEVOPS_ORGANIZATION_URL = os.getenv("AZURE_DEVOPS_ORGANIZATION_URL")
AZURE_DEVOPS_DEFAULT_PROJECT = os.getenv("AZURE_DEVOPS_DEFAULT_PROJECT")

# Validate required environment variables
if not AZURE_DEVOPS_PAT:
    raise ValueError("AZURE_DEVOPS_PAT environment variable is required")
if not AZURE_DEVOPS_ORGANIZATION_URL:
    raise ValueError("AZURE_DEVOPS_ORGANIZATION_URL environment variable is required")

# Initialize Azure DevOps client connection
credentials = BasicAuthentication('', AZURE_DEVOPS_PAT)
connection = Connection(base_url=AZURE_DEVOPS_ORGANIZATION_URL, creds=credentials)
wit_client = connection.clients.get_work_item_tracking_client()

# Initialize MCP server
mcp = FastMCP(
    "Azure DevOps Ticket Manager",
    description="Create and update tickets (work items) in Azure DevOps"
)


@mcp.tool()
def create_work_item(
        project: str = AZURE_DEVOPS_DEFAULT_PROJECT,
        work_item_type: str = None,
        title: str = None,
        description: Optional[str] = None,
        assigned_to: Optional[str] = None,
        state: Optional[str] = None,
        priority: Optional[int] = None,
        area_path: Optional[str] = None,
        iteration_path: Optional[str] = None,
        tags: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new work item in Azure DevOps.

    Example:
    Create a bug titled 'Fix login button' assigned to 'john@example.com' in the 'MyProject' project.
    """
    # Create a JSON patch document for the work item fields
    patch_document = [{
        "op": "add",
        "path": "/fields/System.Title",
        "value": title
    }]

    # Add optional fields if provided
    if description:
        patch_document.append({
            "op": "add",
            "path": "/fields/System.Description",
            "value": description
        })

    if assigned_to:
        patch_document.append({
            "op": "add",
            "path": "/fields/System.AssignedTo",
            "value": assigned_to
        })

    if state:
        patch_document.append({
            "op": "add",
            "path": "/fields/System.State",
            "value": state
        })

    if priority:
        patch_document.append({
            "op": "add",
            "path": "/fields/Microsoft.VSTS.Common.Priority",
            "value": priority
        })

    if area_path:
        patch_document.append({
            "op": "add",
            "path": "/fields/System.AreaPath",
            "value": area_path
        })

    if iteration_path:
        patch_document.append({
            "op": "add",
            "path": "/fields/System.IterationPath",
            "value": iteration_path
        })

    if tags:
        patch_document.append({
            "op": "add",
            "path": "/fields/System.Tags",
            "value": tags
        })

    # Convert to JsonPatchOperation objects
    json_patch_operations = [JsonPatchOperation(**patch) for patch in patch_document]

    # Create the work item
    created_work_item = wit_client.create_work_item(
        document=json_patch_operations,
        project=project,
        type=work_item_type,
        validate_only=False,
        bypass_rules=False,
        suppress_notifications=False
    )

    return {
        "id": created_work_item.id,
        "url": created_work_item.url,
        "title": created_work_item.fields["System.Title"],
        "created_by": created_work_item.fields.get("System.CreatedBy", ""),
        "state": created_work_item.fields.get("System.State", ""),
        "type": work_item_type
    }


@mcp.tool()
def update_work_item(
        work_item_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        assigned_to: Optional[str] = None,
        state: Optional[str] = None,
        priority: Optional[int] = None,
        area_path: Optional[str] = None,
        iteration_path: Optional[str] = None,
        tags: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing work item in Azure DevOps.

    Example:
    Update work item #1234 to change its state to 'Resolved' and assign it to 'jane@example.com'.
    """
    # Create a JSON patch document for the work item fields
    patch_document = []

    # Add optional fields if provided
    if title:
        patch_document.append({
            "op": "add",
            "path": "/fields/System.Title",
            "value": title
        })

    if description:
        patch_document.append({
            "op": "add",
            "path": "/fields/System.Description",
            "value": description
        })

    if assigned_to:
        patch_document.append({
            "op": "add",
            "path": "/fields/System.AssignedTo",
            "value": assigned_to
        })

    if state:
        patch_document.append({
            "op": "add",
            "path": "/fields/System.State",
            "value": state
        })

    if priority:
        patch_document.append({
            "op": "add",
            "path": "/fields/Microsoft.VSTS.Common.Priority",
            "value": priority
        })

    if area_path:
        patch_document.append({
            "op": "add",
            "path": "/fields/System.AreaPath",
            "value": area_path
        })

    if iteration_path:
        patch_document.append({
            "op": "add",
            "path": "/fields/System.IterationPath",
            "value": iteration_path
        })

    if tags:
        patch_document.append({
            "op": "add",
            "path": "/fields/System.Tags",
            "value": tags
        })

    # Only proceed if there are fields to update
    if not patch_document:
        return {"error": "No fields provided for update"}

    # Convert to JsonPatchOperation objects
    json_patch_operations = [JsonPatchOperation(**patch) for patch in patch_document]

    # Update the work item
    updated_work_item = wit_client.update_work_item(
        document=json_patch_operations,
        id=work_item_id,
        validate_only=False,
        bypass_rules=False,
        suppress_notifications=False
    )

    return {
        "id": updated_work_item.id,
        "url": updated_work_item.url,
        "title": updated_work_item.fields.get("System.Title", ""),
        "assigned_to": updated_work_item.fields.get("System.AssignedTo", ""),
        "state": updated_work_item.fields.get("System.State", ""),
        "updated_by": updated_work_item.fields.get("System.ChangedBy", "")
    }


@mcp.tool()
def add_work_item_comment(
        work_item_id: int,
        comment: str
) -> Dict[str, Any]:
    """
    Add a comment to an existing work item in Azure DevOps.

    Example:
    Add a comment to work item #1234 explaining the fix that was implemented.
    """
    # Create a JSON patch document for the comment
    patch_document = [
        {
            "op": "add",
            "path": "/fields/System.History",
            "value": comment
        }
    ]

    # Convert to JsonPatchOperation objects
    json_patch_operations = [JsonPatchOperation(**patch) for patch in patch_document]

    # Add the comment
    updated_work_item = wit_client.update_work_item(
        document=json_patch_operations,
        id=work_item_id,
        validate_only=False,
        bypass_rules=False,
        suppress_notifications=False
    )

    return {
        "id": updated_work_item.id,
        "url": updated_work_item.url,
        "comment_added": True,
        "title": updated_work_item.fields.get("System.Title", ""),
        "state": updated_work_item.fields.get("System.State", "")
    }


@mcp.tool()
def get_work_item(
        work_item_id: int
) -> Dict[str, Any]:
    """
    Get details of an existing work item in Azure DevOps.

    Example:
    Get details of work item #1234.
    """
    # Get the work item
    work_item = wit_client.get_work_item(work_item_id)

    # Extract common fields
    result = {
        "id": work_item.id,
        "url": work_item.url,
        "title": work_item.fields.get("System.Title", ""),
        "state": work_item.fields.get("System.State", ""),
        "type": work_item.fields.get("System.WorkItemType", ""),
        "assigned_to": work_item.fields.get("System.AssignedTo", ""),
        "created_date": work_item.fields.get("System.CreatedDate", ""),
        "created_by": work_item.fields.get("System.CreatedBy", ""),
        "description": work_item.fields.get("System.Description", "")
    }

    # Add other available fields
    for field_name, field_value in work_item.fields.items():
        if field_name not in ["System.Title", "System.State", "System.WorkItemType",
                              "System.AssignedTo", "System.CreatedDate", "System.CreatedBy",
                              "System.Description"]:
            # Convert field name to a more readable format for JSON
            simple_name = field_name.split(".")[-1]
            result[simple_name] = field_value

    return result


if __name__ == "__main__":
    # Run the MCP server with stdio transport
    mcp.run()
