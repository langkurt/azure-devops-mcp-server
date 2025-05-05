"""Search work items tool for Azure DevOps."""

from typing import Dict, List, Any

from utils.config import AZURE_DEVOPS_DEFAULT_PROJECT
from utils.helpers import execute_wiql_query


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