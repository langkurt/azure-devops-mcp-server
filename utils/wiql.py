"""WIQL query building and execution helper functions for Azure DevOps operations."""

from azure.devops.v7_1.work_item_tracking.models import Wiql
from utils.config import wit_client


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


async def execute_wiql_query(query):
    """Execute a WIQL query and return the work items."""
    wiql = Wiql(query=query)
    query_result = wit_client.query_by_wiql(wiql)

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