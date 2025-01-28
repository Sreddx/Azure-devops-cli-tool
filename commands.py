from AzureDevOps import AzureDevOps
import json
import re

class AzureDevOpsCommands(AzureDevOps):
    """
    A class that implements specific Azure DevOps functionalities.
    """
    def list_projects(self):
        """
        Lists all projects in the organization.
        """
        print("Fetching list of projects...")
        endpoint = "_apis/projects?api-version=7.0"
        response = self.handle_request("GET", endpoint)
        projects = response.get('value', [])
        if projects:
            for project in projects:
                print(f"Project Name: {project['name']}")
                print(f"Project ID: {project['id']}")
                print(f"Description: {project.get('description', 'No description')}")
                print("-" * 40)
        else:
            print("No projects found.")

    def create_service_hook(self, project_id, event_type, url):
        """
        Creates a service hook for the given project.
        """
        print(f"Creating service hook for project ID: {project_id}...")
        endpoint = "_apis/hooks/subscriptions?api-version=6.0"
        subscription_data = {
            "publisherId": "tfs",
            "eventType": event_type,
            "resourceVersion": "1.0",
            "consumerId": "webHooks",
            "consumerActionId": "httpRequest",
            "publisherInputs": {
                "projectId": project_id
            },
            "consumerInputs": {
                "url": url
            }
        }
        self.handle_request("POST", endpoint, subscription_data)
        print(f"Service hook created successfully for project ID: {project_id}")

    def list_projects_with_tag_filter(self, target_tags):
        """
        Lists projects with specific tags in their descriptions.

        Args:
            target_tags (list): List of tags to filter projects by.
        """
        print("Fetching projects with tags:", target_tags)
        endpoint = "_apis/projects?api-version=7.0"
        response = self.handle_request("GET", endpoint)
        projects = response.get('value', [])

        filtered_projects = []
        for project in projects:
            description = project.get("description", "")
            try:
                # Extract JSON metadata from the description using regex
                match = re.search(r"\{.*\"tags\":.*\}", description)
                if match:
                    metadata = json.loads(match.group())
                    project_tags = metadata.get("tags", [])
                    # Check if any target tag matches the project's tags
                    if any(tag in project_tags for tag in target_tags):
                        filtered_projects.append(project)
            except (json.JSONDecodeError, AttributeError):
                # Skip projects without valid JSON metadata
                continue

        if filtered_projects:
            for project in filtered_projects:
                print(f"Project Name: {project['name']}")
                print(f"Project ID: {project['id']}")
                print(f"Description: {project.get('description', 'No description')}")
                print("-" * 40)
            return filtered_projects
        else:
            print("No projects matched the specified tags.")
            
    def create_hooks_for_filtered_projects(self, target_tags, event_type, url):
        """
        Creates service hooks for projects that match the specified tags.

        Args:
            target_tags (list): List of tags to filter projects by.
            event_type (str): The event type for the service hook (e.g., 'workitem.created').
            url (str): The webhook URL for the service hook.
        """
        print("Creating service hooks for filtered projects...")
        filtered_projects = self.list_projects_with_tag_filter(target_tags)
        print("Service hook for projects:")
        print(filtered_projects)
        if not filtered_projects:
            print("No projects found with the specified tags. No service hooks will be created.")
            return

        for project in filtered_projects:
            project_id = project["id"]
            self.create_service_hook(project_id, event_type, url)

        print("Service hooks created for all matching projects.")