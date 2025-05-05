"""Update work item tool for Azure DevOps."""

from typing import Dict, Optional, Any

from azure.devops.v7_1.work_item_tracking.models import JsonPatchOperation
from utils.config import wit_client
from utils.helpers import process_tags


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