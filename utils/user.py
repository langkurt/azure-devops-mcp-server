"""User-related helper functions for Azure DevOps operations."""
import base64
from typing import Dict, Any

import requests

from utils.config import AZURE_DEVOPS_PAT, AZURE_DEVOPS_ORGANIZATION_URL


async def get_current_user() -> Dict[str, Any]:
    """
    Get the current authenticated user's details using a direct REST API call.
    More reliable than using the Azure DevOps Python SDK for user details.

    Returns:
        Dict containing user id, display_name, and email
    """
    try:
        # Create an authorization header with PAT
        auth_header = str(base64.b64encode(f":{AZURE_DEVOPS_PAT}".encode("utf-8")), "utf-8")

        # Set up headers for an API request
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # Make an API request to get connection data (user info)
        connection_data_url = f"{AZURE_DEVOPS_ORGANIZATION_URL}/_apis/ConnectionData"
        response = requests.get(connection_data_url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            connection_data = response.json()

            # Extract authenticated user info
            authenticated_user = connection_data.get('authenticatedUser', {})

            # Get email from properties (could be in different places depending on ADO configuration)
            email = None
            if 'properties' in authenticated_user:
                properties = authenticated_user['properties']
                # Try common locations for email
                if 'Account' in properties and '$value' in properties['Account']:
                    email = properties['Account']['$value']
                elif 'Mail' in properties and '$value' in properties['Mail']:
                    email = properties['Mail']['$value']

            return {
                "id": authenticated_user.get('id', ''),
                "display_name": authenticated_user.get('displayName', ''),
                "email": email or ''
            }
        else:
            # Return error information in the appropriate format for MCP
            return {
                "error": f"Failed to get user via REST API. Status code: {response.status_code}",
                "details": response.text if hasattr(response, 'text') else "No additional details"
            }
    except Exception as e:
        # Return error information in the appropriate format for MCP
        return {
            "error": f"Error getting current user via REST API: {str(e)}",
            "details": "Check Azure DevOps PAT and organization URL configuration"
        }
