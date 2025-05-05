"""Helper functions for Azure DevOps operations."""

from typing import Optional, List
from datetime import datetime
from azure.devops.v7_1.work_item_tracking.models import Wiql

from utils.config import core_client, work_client, wit_client, AZURE_DEVOPS_DEFAULT_TEAM


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