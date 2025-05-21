# Use Python 3.10+ as base image
FROM python:3.10-slim

# Environment variables to prevent Python from writing .pyc files 
# and to ensure output is logged directly
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

#Install System dependencies required for building python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY main.py .
COPY tools/ ./tools/
COPY utils/ ./utils/
COPY .env.template ./.env

# Expose port for MCP server
EXPOSE 8000

# Set environment variables (these will be overridden by actual values at runtime)
ENV AZURE_DEVOPS_PAT=your_personal_access_token_here
ENV AZURE_DEVOPS_ORGANIZATION_URL=https://dev.azure.com/your-organization
ENV AZURE_DEVOPS_DEFAULT_PROJECT=your-default-project-name
ENV AZURE_DEVOPS_DEFAULT_TEAM=your-default-team-name
ENV LOG_LEVEL=INFO

# Run the MCP server
CMD ["python", "main.py"]