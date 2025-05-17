"""Iteration-related helper functions for Azure DevOps operations."""
from utils.config import work_client, AZURE_DEVOPS_DEFAULT_PROJECT, AZURE_DEVOPS_DEFAULT_TEAM
from azure.devops.v7_1.work.models import TeamContext


async def get_team_sprint_iterations(project=None, team=None):
    """
    Get the current, next, and recent past sprint iterations for a team.

    Args:
        project (str): Project name (defaults to value from config)
        team (str): Team name (defaults to value from config)

    Returns:
        dict: A dictionary containing current_iteration, next_iteration, and previous_iteration
    """
    # Use defaults if not provided
    project = project or AZURE_DEVOPS_DEFAULT_PROJECT
    team = team or AZURE_DEVOPS_DEFAULT_TEAM

    # Get all team iterations
    team_context = TeamContext(project=project, team=team)
    iterations = work_client.get_team_iterations(team_context=team_context)

    # Filter out iterations without attributes
    valid_iterations = [i for i in iterations if hasattr(i, 'attributes') and i.attributes]

    current_iteration = None
    next_iteration = None
    previous_iteration = None
    current_index = None

    # First attempt: Find by time_frame attribute
    for i, iteration in enumerate(valid_iterations):
        if getattr(iteration.attributes, 'time_frame', None) == 'current':
            current_iteration = iteration
            current_index = i
            break

    # If we found the current iteration by time_frame, get adjacent iterations by index
    if current_index is not None:
        if current_index > 0:
            previous_iteration = valid_iterations[current_index - 1]
        if current_index < len(valid_iterations) - 1:
            next_iteration = valid_iterations[current_index + 1]

    # Second attempt: If time_frame didn't work, use date comparison
    if current_iteration is None:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        for i, iteration in enumerate(valid_iterations):
            start_date = iteration.attributes.start_date
            end_date = iteration.attributes.finish_date

            # Ensure dates have timezone info
            if start_date and start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=timezone.utc)
            if end_date and end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=timezone.utc)

            if start_date and end_date and start_date <= now <= end_date:
                current_iteration = iteration

                # Get adjacent iterations
                if i > 0:
                    previous_iteration = valid_iterations[i - 1]
                if i < len(valid_iterations) - 1:
                    next_iteration = valid_iterations[i + 1]

                break

    return {
        "current_iteration": current_iteration,
        "next_iteration": next_iteration,
        "previous_iteration": previous_iteration
    }