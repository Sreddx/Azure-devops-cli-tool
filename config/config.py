import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

class Config:
    """Configuration class for Azure DevOps CLI tool."""
    
    # Azure DevOps settings
    AZURE_DEVOPS_ORG = os.getenv("AZURE_DEVOPS_ORG", "")
    AZURE_DEVOPS_PAT = os.getenv("AZURE_DEVOPS_PAT", "")
    
    # Project IDs for standard hook creation (comma-separated)
    STANDARD_HOOK_PROJECT_IDS_STR = os.getenv("STANDARD_HOOK_PROJECT_IDS", "")
    
    # Default webhook URLs for different event types
    DEFAULT_WEBHOOK_URLS = {
        "workitem.updated": os.getenv("AZURE_DEVOPS_WORKITEM_WEBHOOK_URL", "https://default-workitem-webhook-url.com"),
        "build.complete": os.getenv("AZURE_DEVOPS_BUILD_WEBHOOK_URL", "https://default-build-webhook-url.com"),
        "release.deployment.completed": os.getenv("AZURE_DEVOPS_RELEASE_WEBHOOK_URL", "https://default-release-webhook-url.com"),
    }
    
    # API versions
    API_VERSION = {
        "projects": "7.0",
        "work_items": "7.1",
        "hooks": "6.0",
        "service_endpoints": "7.1",
        "wiql": "7.0",
        "audit": "7.1-preview.1"
    }
    
    # Default event types
    DEFAULT_EVENT_TYPES = [
        "workitem.updated",
        "build.complete",
        "release.deployment.completed"
    ]
    
    # Default work item types
    DEFAULT_WORK_ITEM_TYPES = [
        "Bug",
        "Task",
        "User Story",
        "Feature"
    ]
    
    @classmethod
    def get_standard_hook_project_ids(cls):
        """Get the list of project IDs for standard hook creation from the .env file."""
        if not cls.STANDARD_HOOK_PROJECT_IDS_STR:
            return []
        # Split by comma, strip whitespace, and filter out empty strings
        ids = [id.strip() for id in cls.STANDARD_HOOK_PROJECT_IDS_STR.split(',') if id.strip()]
        return ids
    
    @classmethod
    def get_webhook_url(cls, event_type):
        """Get the webhook URL for a specific event type."""
        return cls.DEFAULT_WEBHOOK_URLS.get(event_type, cls.DEFAULT_WEBHOOK_URLS["workitem.updated"])
    
    @classmethod
    def validate_credentials(cls):
        """Validate that required credentials are set."""
        if not cls.AZURE_DEVOPS_ORG:
            raise ValueError("Azure DevOps organization is required. Set AZURE_DEVOPS_ORG environment variable.")
        if not cls.AZURE_DEVOPS_PAT:
            raise ValueError("Azure DevOps personal access token is required. Set AZURE_DEVOPS_PAT environment variable.") 