"""Get work items assigned to current user in sprints tool for Azure DevOps."""

from typing import Dict, List, Any

from utils.config import AZURE_DEVOPS_DEFAULT_PROJECT
from utils.helpers import get_current_user, get_team_iterations, build_wiql_query, execute_wiql_query


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