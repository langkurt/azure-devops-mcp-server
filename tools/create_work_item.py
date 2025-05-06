"""Create work item tool for Azure DevOps."""

from typing import Dict, Optional, Any

from azure.devops.v7_1.work_item_tracking.models import JsonPatchOperation
from utils.config import wit_client, AZURE_DEVOPS_DEFAULT_PROJECT
from utils.tags import process_tags


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
    - When closing a work item, do not attempt to set remaining_work=0 directly
    - Instead, first check the current state using get_work_item and then:
      * If moving from 'New' or 'Active' to 'Closed', update the state first without changing remaining_work
      * Once the state is updated to 'Closed', Azure DevOps will handle the remaining work automatically
    - If you need to update original_estimate for a work item that has no value set, always set both
      original_estimate and remaining_work to the same value before attempting to close the item
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