"""User-related helper functions for Azure DevOps operations."""

from utils.config import core_client


async def get_current_user():
    """Get the current authenticated user's details."""
    # Using the core client to get connection data which includes authorized user info
    connection_data = core_client.get_connection_data()
    authenticated_user = connection_data.authenticated_user
    return {
        "id": authenticated_user.id,
        "display_name": authenticated_user.display_name,
        "email": authenticated_user.properties.get("Mail", "")
    }