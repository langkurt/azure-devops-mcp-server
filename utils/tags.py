"""Tag processing helper functions for Azure DevOps operations."""

from typing import Optional


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