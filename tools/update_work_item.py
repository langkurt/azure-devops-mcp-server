"""Update work item tool for Azure DevOps."""

from typing import Dict, Optional, Any

from azure.devops.v7_1.work_item_tracking.models import JsonPatchOperation
from utils.config import wit_client
from utils.tags import process_tags


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

     Note:
    - Tags are limited to a maximum of 3
    - Estimates are in hours
    - When closing a work item, do not attempt to set remaining_work=0 directly
    - Instead, first check the current state using get_work_item and then:
      * If moving from 'New' or 'Active' to 'Closed', update the state first without changing remaining_work
      * Once the state is updated to 'Closed', Azure DevOps will handle the remaining work automatically
    - If you need to update original_estimate for a work item that has no value set, always set both
      original_estimate and remaining_work to the same value before attempting to close the item
    """
    # Define field mapping
    field_mapping = {
        "System.Title": title,
        "System.Description": description,
        "System.AssignedTo": assigned_to,
        "System.State": state,
        "Microsoft.VSTS.Common.Priority": priority,
        "System.AreaPath": area_path,
        "System.IterationPath": iteration_path,
        "System.Tags": process_tags(tags, max_tags=3),
        "Microsoft.VSTS.Scheduling.OriginalEstimate": original_estimate,
        "Microsoft.VSTS.Scheduling.RemainingWork": remaining_work
    }

    # Create the patch document: If a field has a value, add it to the request
    patch_document = []
    for path, value in field_mapping.items():
        if value is not None:
            patch_document.append({
                "op": "add",
                "path": f"/fields/{path}",
                "value": value
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

    # Extract fields for response
    fields = updated_work_item.fields

    # Build basic response
    response = {
        "id": updated_work_item.id,
        "url": updated_work_item.url,
        "title": fields["System.Title"],
        "created_by": fields.get("System.CreatedBy", ""),
        "state": fields.get("System.State", ""),
        "original_estimate": fields.get("Microsoft.VSTS.Scheduling.OriginalEstimate", ""),
        "remaining_work": fields.get("Microsoft.VSTS.Scheduling.RemainingWork", ""),
        "tags": fields.get("System.Tags", ""),
    }

    return response