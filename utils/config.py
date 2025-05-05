"""Configuration and initialization for Azure DevOps client."""

import os
from dotenv import load_dotenv
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

# Load environment variables from .env file
load_dotenv()

# Get Azure DevOps configuration from environment variables
AZURE_DEVOPS_PAT = os.getenv("AZURE_DEVOPS_PAT")
AZURE_DEVOPS_ORGANIZATION_URL = os.getenv("AZURE_DEVOPS_ORGANIZATION_URL")
AZURE_DEVOPS_DEFAULT_PROJECT = os.getenv("AZURE_DEVOPS_DEFAULT_PROJECT")
AZURE_DEVOPS_DEFAULT_TEAM = os.getenv("AZURE_DEVOPS_DEFAULT_TEAM")

# Validate required environment variables
if not AZURE_DEVOPS_PAT:
    raise ValueError("AZURE_DEVOPS_PAT environment variable is required")
if not AZURE_DEVOPS_ORGANIZATION_URL:
    raise ValueError("AZURE_DEVOPS_ORGANIZATION_URL environment variable is required")

# Initialize Azure DevOps client connection
credentials = BasicAuthentication('', AZURE_DEVOPS_PAT)
connection = Connection(base_url=AZURE_DEVOPS_ORGANIZATION_URL, creds=credentials)
wit_client = connection.clients.get_work_item_tracking_client()
core_client = connection.clients.get_core_client()
work_client = connection.clients.get_work_client()
identity_client = connection.clients_v7_1.get_identity_client()