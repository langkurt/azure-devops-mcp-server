"""Iteration-related helper functions for Azure DevOps operations."""

from datetime import datetime
from utils.config import work_client, AZURE_DEVOPS_DEFAULT_TEAM


async def get_team_iterations(project, team=None):
    """Get all iterations for a team."""
    team_context = work_client.TeamContext(project=project, team=team or AZURE_DEVOPS_DEFAULT_TEAM)
    iterations = work_client.get_team_iterations(team_context=team_context)

    # Find current and future iterations based on date
    now = datetime.now()
    current_iteration = None
    next_iteration = None

    sorted_iterations = sorted(iterations, key=lambda x: x.attributes.start_date)

    for i, iteration in enumerate(sorted_iterations):
        if iteration.attributes.start_date <= now <= iteration.attributes.finish_date:
            current_iteration = iteration
            if i + 1 < len(sorted_iterations):
                next_iteration = sorted_iterations[i + 1]
            break
        elif iteration.attributes.start_date > now:
            if not next_iteration:
                next_iteration = iteration
            break

    return {
        "all_iterations": iterations,
        "current_iteration": current_iteration,
        "next_iteration": next_iteration
    }