"""Add comment to work item tool for Azure DevOps."""

from typing import Dict, Any

from azure.devops.v7_1.work_item_tracking.models import JsonPatchOperation
from utils.config import wit_client


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