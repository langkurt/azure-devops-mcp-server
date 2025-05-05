# Azure DevOps MCP Server

This project implements a Model Context Protocol (MCP) server that enables AI assistants to interact with Azure DevOps for creating and updating tickets (work items). The server acts as a bridge between LLMs and the Azure DevOps REST API, providing a standardized way for AI agents to manage work items.

## Overview

Model Context Protocol (MCP) is an open standard that standardizes how applications provide context to Large Language Models (LLMs). It creates a common interface for LLMs to interact with external tools and services, eliminating the need for custom integrations between different AI models and tools.

This MCP server specifically focuses on ticket management in Azure DevOps, enabling AI assistants to:
- Create new work items (tickets)
- Update existing work items
- Add comments to work items
- Retrieve work item details

## Prerequisites

- Python 3.10+
- Azure DevOps account with appropriate permissions
- Personal Access Token (PAT) with necessary scopes for Azure DevOps API access

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/langkurt/azure-devops-mcp-server.git
   cd azure-devops-mcp-server
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with the following variables:
   ```
   AZURE_DEVOPS_PAT=your_personal_access_token
   AZURE_DEVOPS_ORGANIZATION_URL=https://dev.azure.com/your-organization
   AZURE_DEVOPS_DEFAULT_PROJECT=your-default-project
   ```

   Note: Make sure to provide the full URL to your Azure DevOps organization.

## Usage

### Running the MCP Server

You can run the MCP server in different ways:

1. Development mode with the MCP Inspector:
   ```bash
   mcp dev main.py
   ```

2. Install in Claude Desktop:
   ```bash
   mcp install main.py --name "Azure DevOps Ticket Manager"
   ```

3. Run directly:
   ```bash
   python main.py
   ```

### Configuring with Claude or Other AI Assistants

To configure this MCP server with Claude Desktop, add the following to your Claude Desktop configuration file:

```json
{
  "mcpServers": {
    "azureDevOpsTickets": {
      "command": "python",
      "args": ["path/to/server.py"],
      "env": {
        "AZURE_DEVOPS_PAT": "your_personal_access_token",
        "AZURE_DEVOPS_ORGANIZATION_URL": "https://dev.azure.com/your-organization",
        "AZURE_DEVOPS_DEFAULT_PROJECT": "your-default-project"
      }
    }
  }
}
```

### Example Prompts for AI Assistants

Once the MCP server is running and connected to your AI assistant, you can use prompts like:

- "Create a bug in the ProjectX with the title 'Login button not working in Safari' and assign it to jane@example.com"
- "Update work item #1234 to change its status to 'Resolved' and add a comment explaining the fix"
- "Get details about work item #5678"
- "Create a new user story for implementing two-factor authentication"

## Available Tools

### create_work_item

Creates a new work item in Azure DevOps.

Parameters:
- `project`: The project in which to create the work item (defaults to the value in .env)
- `work_item_type`: The type of work item to create (e.g., 'Bug', 'Task', 'User Story')
- `title`: Title of the work item
- `description` (optional): Description of the work item
- `assigned_to` (optional): Email of the person to assign the work item to
- `state` (optional): Initial state of the work item
- `priority` (optional): Priority of the work item
- `area_path` (optional): Area path for the work item
- `iteration_path` (optional): Iteration path for the work item
- `tags` (optional): Comma-separated list of tags

### update_work_item

Updates an existing work item in Azure DevOps.

Parameters:
- `work_item_id`: ID of the work item to update
- `title` (optional): New title for the work item
- `description` (optional): New description for the work item
- `assigned_to` (optional): Email of the person to assign the work item to
- `state` (optional): New state of the work item
- `priority` (optional): New priority of the work item
- `area_path` (optional): New area path for the work item
- `iteration_path` (optional): New iteration path for the work item
- `tags` (optional): Comma-separated list of tags

### add_work_item_comment

Adds a comment to an existing work item in Azure DevOps.

Parameters:
- `work_item_id`: ID of the work item to add a comment to
- `comment`: Comment text to add to the work item

### get_work_item

Gets details of an existing work item in Azure DevOps.

Parameters:
- `work_item_id`: ID of the work item to retrieve

## Security Considerations

- This MCP server requires a Personal Access Token (PAT) with appropriate permissions to the Azure DevOps organization.
- Store your PAT securely and never commit it to version control.
- The server should be run in a secure environment to prevent unauthorized access to your Azure DevOps resources.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Anthropic](https://www.anthropic.com/) for developing the Model Context Protocol
- [Microsoft](https://learn.microsoft.com/en-us/azure/devops/) for the Azure DevOps API
- [Azure DevOps Python API](https://github.com/microsoft/azure-devops-python-api)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
