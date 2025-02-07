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
            
    def list_subscriptions(self, project_id): #Suscriptions are like webhooks
        """
        Lists service hook subscriptions for the specified project ID.
        """
        if not project_id:
            print("Error: --project-id is required to list subscriptions.")
            return

        print(f"Listing subscriptions for project ID: {project_id} ...")

        # We can filter subscriptions by `publisherId=tfs` and `publisherInputFilters=projectId=<GUID>`
        endpoint = f"_apis/hooks/subscriptions?publisherId=tfs&publisherInputFilters=projectId={project_id}&api-version=7.1"

        # Make the GET request
        response = self.handle_request("GET", endpoint)
        subscriptions = response.get("value", [])

        if not subscriptions:
            print("No service hook subscriptions found for this project.")
            return

        for sub in subscriptions:
            if sub.get('eventType') == "workitem.updated":
                print(f"Subscription ID: {sub['id']}")
                print(f"Event Type:     {sub.get('eventType', 'N/A')}")
                print(f"Publisher ID:   {sub.get('publisherId', 'N/A')}")
                print(f"URL:            {sub['consumerInputs'].get('url', 'N/A')}")
                print(f"Status:         {sub.get('status', 'N/A')}")
                print(f"Created Date:   {sub.get('createdDate', 'N/A')}")
                # Print more fields as needed
                print("-" * 40)
                print("===== Subscription =====")
                print(json.dumps(sub, indent=2))


    def create_service_hook(self, project_id, event_type, hook_url, state_changed=False):
        print(f"Creating service hook for project ID: {project_id} with event: {event_type}")
        endpoint = "_apis/hooks/subscriptions?api-version=6.0"
        
        subscription_data = {
            "publisherId": "tfs",
            "eventType": event_type,
            "resourceVersion": "1.0",
            "consumerId": "webHooks",
            "consumerActionId": "httpRequest",
            "publisherInputs": {
                "projectId": project_id,   # Must be the GUID as a string
                "areaPath": "",
                "workItemType": "",
            },
            "consumerInputs": {
                "url": hook_url
            }
        }


        # If user wants only State=Closed AND event_type is workitem.updated
        if state_changed and event_type == "workitem.updated":
            subscription_data["publisherInputs"]["changedFields"] = "System.State"

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

    def create_hooks_for_filtered_projects(self, target_tags, event_type, hook_url, state_changed):
        """
        Creates service hooks for projects that match the specified tags.

        Args:
            target_tags (list): List of tags to filter projects by.
            event_type (str): The event type for the service hook (e.g., 'workitem.updated').
            url (str): The webhook URL for the service hook.
            filter_fields (bool): If True, hooks will be created with specific field tracking.
        """
        print(f"Creating service hooks for projects with tags: {target_tags}")

        # Filter projects by tags
        filtered_projects = self.list_projects_with_tag_filter(target_tags)
        if not filtered_projects:
            print("No projects found with the specified tags. No service hooks will be created.")
            return

        # Iterate over filtered projects and create service hooks
        for project in filtered_projects:
            project_id = project["id"]
            print(f"Creating hook for project: {project['name']} (ID: {project_id})")

            self.create_service_hook(project_id, event_type, hook_url, state_changed)

        print("Service hooks created for all matching projects.")

    def list_and_update_webhooks(self, target_tags):
        """
        Lists all projects filtered by tags and upgrades their webhooks to resourceVersion: '1.0'.

        Args:
            target_tags (list): List of tags to filter projects by.
        """
        # Reuse the existing list_projects_with_tag_filter method
        print(f"Filtering projects by tags: {target_tags}")
        filtered_projects = self.list_projects_with_tag_filter(target_tags)

        if not filtered_projects:
            print("No projects matched the specified tags.")
            return

        # Upgrade webhooks for filtered projects
        for project in filtered_projects:
            project_id = project["id"]
            print(f"Upgrading webhooks for project: {project['name']} (ID: {project_id})")

            # Get subscriptions
            endpoint = f"_apis/hooks/subscriptions?publisherId=tfs&publisherInputFilters=projectId={project_id}&api-version=7.1"
            response = self.handle_request("GET", endpoint)
            subscriptions = response.get("value", [])

            if not subscriptions:
                print(f"No webhooks found for project {project['name']} (ID: {project_id}).")
                continue

            # Update webhooks
            for sub in subscriptions:
                if sub.get("eventType") == "workitem.updated":
                    subscription_id = sub["id"]
                    sub["resourceVersion"] = "1.0"  # Update the resourceVersion to 1.0

                    # Update the webhook
                    update_endpoint = f"_apis/hooks/subscriptions/{subscription_id}?api-version=6.0"
                    self.handle_request("PUT", update_endpoint, sub)
                    print(f"Updated webhook {subscription_id} for project {project['name']} to resourceVersion: 1.0")

        print("All applicable webhooks have been updated.")


                
                    
            



