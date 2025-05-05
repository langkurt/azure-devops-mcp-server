"""Get work item tool for Azure DevOps."""

from typing import Dict, Any

from utils.config import wit_client


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