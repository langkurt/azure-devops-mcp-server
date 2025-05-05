"""
Azure DevOps MCP Server for Ticket Management

This MCP server implements functionality to create and update tickets (work items) 
in Azure DevOps through a standardized Model Context Protocol interface.
"""

import os
from typing import Dict, Optional, Any, List

from azure.devops.connection import Connection
from azure.devops.v7_1.work_item_tracking.models import JsonPatchOperation, Wiql
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from msrest.authentication import BasicAuthentication
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Get Azure DevOps configuration from environment variables
AZURE_DEVOPS_PAT = os.getenv("AZURE_DEVOPS_PAT")
AZURE_DEVOPS_ORGANIZATION_URL = os.getenv("AZURE_DEVOPS_ORGANIZATION_URL")
AZURE_DEVOPS_DEFAULT_PROJECT = os.getenv("AZURE_DEVOPS_DEFAULT_PROJECT")
AZURE_DEVOPS_DEFAULT_TEAM = os.getenv("AZURE_DEVOPS_DEFAULT_TEAM")

# Validate required environment variables
if not AZURE_DEVOPS_PAT:
    raise ValueError("AZURE_DEVOPS_PAT environment variable is required")
if not AZURE_DEVOPS_ORGANIZATION_URL:
    raise ValueError("AZURE_DEVOPS_ORGANIZATION_URL environment variable is required")

# Initialize Azure DevOps client connection
credentials = BasicAuthentication('', AZURE_DEVOPS_PAT)
connection = Connection(base_url=AZURE_DEVOPS_ORGANIZATION_URL, creds=credentials)
wit_client = connection.clients.get_work_item_tracking_client()
core_client = connection.clients.get_core_client()
work_client = connection.clients.get_work_client()
identity_client = connection.clients_v7_1.get_identity_client()

# Initialize MCP server
mcp = FastMCP(
    "Azure DevOps Ticket Manager",
    description="Create and update tickets (work items) in Azure DevOps"
)


# Helper functions for querying work items

async def get_current_user():
    """Get the current authenticated user's details."""
    # Using the core client to get connection data which includes authorized user info
    connection_data = core_client.get_connection_data()
    authenticated_user = connection_data.authenticated_user
    return {
        "id": authenticated_user.id,
        "display_name": authenticated_user.display_name,
        "email": authenticated_user.properties.get("Mail", "")
    }


async def get_team_iterations(project, team=None):
    """Get all iterations for a team."""
    team_context = work_client.TeamContext(project=project, team=team or AZURE_DEVOPS_DEFAULT_TEAM)
    iterations = work_client.get_team_iterations(team_context=team_context)

    # Find current and future iterations based on date
    now = datetime.now()
    current_iteration = None
    next_iteration = None

    sorted_iterations = sorted(iterations, key=lambda x: x.attributes.start_date)

    for i, iteration in enumerate(sorted_iterations):
        if iteration.attributes.start_date <= now <= iteration.attributes.finish_date:
            current_iteration = iteration
            if i + 1 < len(sorted_iterations):
                next_iteration = sorted_iterations[i + 1]
            break
        elif iteration.attributes.start_date > now:
            if not next_iteration:
                next_iteration = iteration
            break

    return {
        "all_iterations": iterations,
        "current_iteration": current_iteration,
        "next_iteration": next_iteration
    }


async def build_wiql_query(project, assigned_to=None, iterations=None, work_item_types=None):
    """Build a WIQL query with the specified filters."""
    query_parts = [f"[System.TeamProject] = '{project}'"]

    if assigned_to:
        query_parts.append(f"[System.AssignedTo] = '{assigned_to}'")

    if iterations:
        iteration_conditions = []
        for iteration in iterations:
            if iteration:
                iteration_path = iteration.path
                iteration_conditions.append(f"[System.IterationPath] UNDER '{iteration_path}'")

        if iteration_conditions:
            query_parts.append("(" + " OR ".join(iteration_conditions) + ")")

    if work_item_types:
        type_conditions = []
        for work_item_type in work_item_types:
            type_conditions.append(f"[System.WorkItemType] = '{work_item_type}'")

        if type_conditions:
            query_parts.append("(" + " OR ".join(type_conditions) + ")")

    query = "SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo], [System.WorkItemType], [System.Tags], [System.IterationPath], [System.CreatedDate] FROM WorkItems WHERE " + " AND ".join(
        query_parts) + " ORDER BY [System.Id]"

    return query


async def execute_wiql_query(query, project=None):
    """Execute a WIQL query and return the work items."""
    wiql = Wiql(query=query)
    query_result = wit_client.query_by_wiql(wiql, project=project)

    if query_result.work_items:
        # Get work item IDs
        work_item_ids = [item.id for item in query_result.work_items]

        # Get detailed work items with specified fields
        work_items = wit_client.get_work_items(
            ids=work_item_ids,
            fields=["System.Id", "System.Title", "System.State", "System.AssignedTo",
                    "System.WorkItemType", "System.Tags", "System.IterationPath",
                    "System.CreatedDate", "Microsoft.VSTS.Scheduling.OriginalEstimate",
                    "Microsoft.VSTS.Scheduling.RemainingWork"]
        )

        return work_items

    return []


def process_tags(tags: Optional[str] = None, max_tags: int = 3) -> Optional[str]:
    """
    Process tags to ensure there are at most the maximum number allowed.

    Args:
        tags: Comma-separated list of tags
        max_tags: Maximum number of tags to allow

    Returns:
        Processed tags string or None if input was None
    """
    if not tags:
        return None

    # Split tags by comma and strip whitespace
    tag_list = [tag.strip() for tag in tags.split(',')]

    # Limit to max_tags
    if len(tag_list) > max_tags:
        tag_list = tag_list[:max_tags]

    # Join back with semicolons as per Azure DevOps tag format
    return '; '.join(tag_list)


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
        tags: Optional[str] = None,
        original_estimate: Optional[float] = None,
        remaining_work: Optional[float] = None
) -> Dict[str, Any]:
    """
    Create a new work item in Azure DevOps with estimates.

    Example:
    Create a bug titled 'Fix login button' assigned to 'john@example.com' in the 'MyProject' project
    with an original estimate of 4 hours and remaining work of 4 hours.

    Note:
    - Tags are limited to a maximum of 3
    - Estimates are in hours
    """
    # Process tags to limit to max 3
    processed_tags = process_tags(tags, max_tags=3)

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

    if processed_tags:
        patch_document.append({
            "op": "add",
            "path": "/fields/System.Tags",
            "value": processed_tags
        })

    # Add estimate fields
    if original_estimate is not None:
        patch_document.append({
            "op": "add",
            "path": "/fields/Microsoft.VSTS.Scheduling.OriginalEstimate",
            "value": original_estimate
        })

    if remaining_work is not None:
        patch_document.append({
            "op": "add",
            "path": "/fields/Microsoft.VSTS.Scheduling.RemainingWork",
            "value": remaining_work
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

    # Prepare response
    response = {
        "id": created_work_item.id,
        "url": created_work_item.url,
        "title": created_work_item.fields["System.Title"],
        "created_by": created_work_item.fields.get("System.CreatedBy", ""),
        "state": created_work_item.fields.get("System.State", ""),
        "type": work_item_type
    }

    # Add estimates to response if provided
    if original_estimate is not None:
        response["original_estimate"] = created_work_item.fields.get("Microsoft.VSTS.Scheduling.OriginalEstimate")

    if remaining_work is not None:
        response["remaining_work"] = created_work_item.fields.get("Microsoft.VSTS.Scheduling.RemainingWork")

    # Add tags if provided
    if processed_tags:
        response["tags"] = created_work_item.fields.get("System.Tags", "")

    return response


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
        tags: Optional[str] = None,
        original_estimate: Optional[float] = None,
        remaining_work: Optional[float] = None
) -> Dict[str, Any]:
    """
    Update an existing work item in Azure DevOps, including estimates.

    Example:
    Update work item #1234 to change its state to 'Resolved', assign it to 'jane@example.com',
    and update remaining work to 2 hours.

    Note:
    - Tags are limited to a maximum of 3
    - Estimates are in hours
    """
    # Process tags to limit to max 3
    processed_tags = process_tags(tags, max_tags=3)

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

    if processed_tags:
        patch_document.append({
            "op": "add",
            "path": "/fields/System.Tags",
            "value": processed_tags
        })

    # Add estimate fields
    if original_estimate is not None:
        patch_document.append({
            "op": "add",
            "path": "/fields/Microsoft.VSTS.Scheduling.OriginalEstimate",
            "value": original_estimate
        })

    if remaining_work is not None:
        patch_document.append({
            "op": "add",
            "path": "/fields/Microsoft.VSTS.Scheduling.RemainingWork",
            "value": remaining_work
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

    # Prepare response
    response = {
        "id": updated_work_item.id,
        "url": updated_work_item.url,
        "title": updated_work_item.fields.get("System.Title", ""),
        "assigned_to": updated_work_item.fields.get("System.AssignedTo", ""),
        "state": updated_work_item.fields.get("System.State", ""),
        "updated_by": updated_work_item.fields.get("System.ChangedBy", "")
    }

    # Add estimates to response if provided
    if original_estimate is not None:
        response["original_estimate"] = updated_work_item.fields.get("Microsoft.VSTS.Scheduling.OriginalEstimate")

    if remaining_work is not None:
        response["remaining_work"] = updated_work_item.fields.get("Microsoft.VSTS.Scheduling.RemainingWork")

    # Add tags if provided
    if processed_tags:
        response["tags"] = updated_work_item.fields.get("System.Tags", "")

    return response


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
        "description": work_item.fields.get("System.Description", ""),
        "original_estimate": work_item.fields.get("Microsoft.VSTS.Scheduling.OriginalEstimate", ""),
        "remaining_work": work_item.fields.get("Microsoft.VSTS.Scheduling.RemainingWork", ""),
        "tags": work_item.fields.get("System.Tags", "")
    }

    # Add other available fields
    for field_name, field_value in work_item.fields.items():
        if field_name not in ["System.Title", "System.State", "System.WorkItemType",
                              "System.AssignedTo", "System.CreatedDate", "System.CreatedBy",
                              "System.Description", "Microsoft.VSTS.Scheduling.OriginalEstimate",
                              "Microsoft.VSTS.Scheduling.RemainingWork", "System.Tags"]:
            # Convert field name to a more readable format for JSON
            simple_name = field_name.split(".")[-1]
            result[simple_name] = field_value

    return result


@mcp.tool()
async def get_my_sprint_work_items(
        project: str = None,
        include_current_sprint: bool = True,
        include_next_sprint: bool = True,
        work_item_types: List[str] = None
) -> Dict[str, Any]:
    """
    Get work items assigned to the current user in the current and/or next sprint.

    Example:
    "What are all the tickets assigned to me in the current sprint and next sprint?"
    """
    project = project or AZURE_DEVOPS_DEFAULT_PROJECT

    if not project:
        return {"error": "No project specified and no default project set"}

    # Get current user
    current_user = await get_current_user()

    # Get iterations
    iterations_data = await get_team_iterations(project)
    current_iteration = iterations_data.get("current_iteration")
    next_iteration = iterations_data.get("next_iteration")

    # Prepare iterations to include in query
    target_iterations = []
    if include_current_sprint and current_iteration:
        target_iterations.append(current_iteration)
    if include_next_sprint and next_iteration:
        target_iterations.append(next_iteration)

    # If no iterations match criteria, return empty result
    if not target_iterations:
        return {
            "user": current_user,
            "work_items": [],
            "message": "No current or next sprint found"
        }

    # Build WIQL query
    query = await build_wiql_query(
        project=project,
        assigned_to=current_user["display_name"],
        iterations=target_iterations,
        work_item_types=work_item_types
    )

    # Execute query
    work_items = await execute_wiql_query(query, project)

    # Format results
    formatted_work_items = []
    iterations_info = {}

    # Prepare iteration info
    if include_current_sprint and current_iteration:
        iterations_info["current_sprint"] = {
            "name": current_iteration.name,
            "path": current_iteration.path,
            "start_date": current_iteration.attributes.start_date,
            "end_date": current_iteration.attributes.finish_date
        }

    if include_next_sprint and next_iteration:
        iterations_info["next_sprint"] = {
            "name": next_iteration.name,
            "path": next_iteration.path,
            "start_date": next_iteration.attributes.start_date,
            "end_date": next_iteration.attributes.finish_date
        }

    # Format work items
    for item in work_items:
        iteration_path = item.fields.get("System.IterationPath", "")
        sprint_type = "unknown"

        if current_iteration and iteration_path.startswith(current_iteration.path):
            sprint_type = "current_sprint"
        elif next_iteration and iteration_path.startswith(next_iteration.path):
            sprint_type = "next_sprint"

        formatted_work_items.append({
            "id": item.id,
            "title": item.fields.get("System.Title", ""),
            "state": item.fields.get("System.State", ""),
            "type": item.fields.get("System.WorkItemType", ""),
            "iteration_path": iteration_path,
            "sprint_type": sprint_type,
            "tags": item.fields.get("System.Tags", ""),
            "original_estimate": item.fields.get("Microsoft.VSTS.Scheduling.OriginalEstimate", ""),
            "remaining_work": item.fields.get("Microsoft.VSTS.Scheduling.RemainingWork", "")
        })

    return {
        "user": current_user,
        "iterations": iterations_info,
        "work_items": formatted_work_items,
        "count": len(formatted_work_items)
    }


@mcp.tool()
async def search_work_items(
        project: str = None,
        assigned_to: str = None,
        iteration_path: str = None,
        work_item_types: List[str] = None,
        states: List[str] = None,
        query: str = None
) -> Dict[str, Any]:
    """
    Search for work items using custom filters.

    Example:
    "Find all active bugs assigned to John in the current project"
    """
    project = project or AZURE_DEVOPS_DEFAULT_PROJECT

    if not project:
        return {"error": "No project specified and no default project set"}

    # If a custom query is provided, use it directly
    if query:
        work_items = await execute_wiql_query(query, project)
    else:
        # Build filters for the query
        filters = [f"[System.TeamProject] = '{project}'"]

        if assigned_to:
            filters.append(f"[System.AssignedTo] = '{assigned_to}'")

        if iteration_path:
            filters.append(f"[System.IterationPath] UNDER '{iteration_path}'")

        if work_item_types and len(work_item_types) > 0:
            type_conditions = [f"[System.WorkItemType] = '{wt}'" for wt in work_item_types]
            filters.append("(" + " OR ".join(type_conditions) + ")")

        if states and len(states) > 0:
            state_conditions = [f"[System.State] = '{s}'" for s in states]
            filters.append("(" + " OR ".join(state_conditions) + ")")

        query = "SELECT [System.Id], [System.Title], [System.State], [System.AssignedTo], [System.WorkItemType], [System.Tags], [System.IterationPath], [System.CreatedDate], [Microsoft.VSTS.Scheduling.OriginalEstimate], [Microsoft.VSTS.Scheduling.RemainingWork] FROM WorkItems WHERE " + " AND ".join(
            filters) + " ORDER BY [System.Id]"

        work_items = await execute_wiql_query(query, project)

    # Format the results
    formatted_work_items = []
    for item in work_items:
        formatted_work_items.append({
            "id": item.id,
            "title": item.fields.get("System.Title", ""),
            "state": item.fields.get("System.State", ""),
            "type": item.fields.get("System.WorkItemType", ""),
            "assigned_to": item.fields.get("System.AssignedTo", {}).get("displayName", "") if item.fields.get(
                "System.AssignedTo") else "",
            "iteration_path": item.fields.get("System.IterationPath", ""),
            "tags": item.fields.get("System.Tags", ""),
            "created_date": item.fields.get("System.CreatedDate", ""),
            "original_estimate": item.fields.get("Microsoft.VSTS.Scheduling.OriginalEstimate", ""),
            "remaining_work": item.fields.get("Microsoft.VSTS.Scheduling.RemainingWork", "")
        })

    return {
        "project": project,
        "work_items": formatted_work_items,
        "count": len(formatted_work_items),
        "query": query
    }

if __name__ == "__main__":
    # Run the MCP server with stdio transport
    print("Starting Azure DevOps MCP Server...")
    mcp.run()