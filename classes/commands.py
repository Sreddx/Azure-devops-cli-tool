from classes.AzureDevOps import AzureDevOps
from config.config import Config
import json
import re
import csv

class AzureDevOpsCommands(AzureDevOps):
    """
    A class that implements specific Azure DevOps functionalities.
    """
    def list_projects(self):
        """
        Lists all projects in the organization.
        """
        print("Fetching list of projects...")
        endpoint = f"_apis/projects?api-version={self.get_api_version('projects')}"
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
            
    def list_subscriptions(self, project_id):
        """
        Lists service hook subscriptions for the specified project ID.
        
        Args:
            project_id (str): The ID of the project to list subscriptions for.
        """
        if not project_id:
            print("Error: --project-id is required to list subscriptions.")
            return

        print(f"Listing subscriptions for project ID: {project_id} ...")
        endpoint = f"_apis/hooks/subscriptions?publisherId=tfs&publisherInputFilters=projectId={project_id}&api-version={self.get_api_version('hooks')}"
        response = self.handle_request("GET", endpoint)
        subscriptions = response.get("value", [])

        if not subscriptions:
            print("No service hook subscriptions found for this project.")
            return

        for sub in subscriptions:
            print(f"Subscription ID: {sub['id']}")
            print(f"Event Type:     {sub.get('eventType', 'N/A')}")
            print(f"Publisher ID:   {sub.get('publisherId', 'N/A')}")
            print(f"URL:            {sub['consumerInputs'].get('url', 'N/A')}")
            print(f"Status:         {sub.get('status', 'N/A')}")
            print(f"Created Date:   {sub.get('createdDate', 'N/A')}")
            print("-" * 40)

    def create_service_hook(self, project_id, event_type, hook_url=None, state_changed=False):
        """
        Creates a service hook for a specific project.
        
        Args:
            project_id (str): The ID of the project to create the hook for.
            event_type (str): The event type that triggers the hook.
            hook_url (str, optional): The webhook URL. If not provided, uses default from config.
            state_changed (bool): If True, only trigger on state changes for workitem.updated.
        """
        if not project_id or not event_type:
            print("Error: --project-id and --event-type are required to create a service hook.")
            return

        hook_url = hook_url or Config.get_webhook_url(event_type)
        print(f"Creating service hook for project ID: {project_id} with event: {event_type}")
        
        endpoint = f"_apis/hooks/subscriptions?api-version={self.get_api_version('hooks')}"
        subscription_data = {
            "publisherId": "tfs",
            "eventType": event_type,
            "resourceVersion": "1.0",
            "consumerId": "webHooks",
            "consumerActionId": "httpRequest",
            "publisherInputs": {
                "projectId": project_id,
                "areaPath": "",
                "workItemType": "",
            },
            "consumerInputs": {
                "url": hook_url
            }
        }

        if state_changed and event_type == "workitem.updated":
            subscription_data["publisherInputs"]["changedFields"] = "System.State"

        self.handle_request("POST", endpoint, subscription_data)
        print(f"Service hook created successfully for project ID: {project_id}")

    def remove_service_hook(self, project_id, subscription_id=None):
        """
        Removes a service hook subscription.
        
        Args:
            project_id (str): The ID of the project containing the hook.
            subscription_id (str, optional): The ID of the subscription to remove. If not provided, removes all subscriptions.
        """
        if not project_id:
            print("Error: --project-id is required to remove a service hook.")
            return

        if subscription_id:
            # Remove specific subscription
            endpoint = f"_apis/hooks/subscriptions/{subscription_id}?api-version={self.get_api_version('hooks')}"
            self.handle_request("DELETE", endpoint)
            print(f"Service hook {subscription_id} removed successfully.")
        else:
            # List all subscriptions and remove them
            endpoint = f"_apis/hooks/subscriptions?publisherId=tfs&publisherInputFilters=projectId={project_id}&api-version={self.get_api_version('hooks')}"
            response = self.handle_request("GET", endpoint)
            subscriptions = response.get("value", [])
            
            if not subscriptions:
                print("No service hook subscriptions found to remove.")
                return
                
            for sub in subscriptions:
                sub_id = sub["id"]
                delete_endpoint = f"_apis/hooks/subscriptions/{sub_id}?api-version={self.get_api_version('hooks')}"
                self.handle_request("DELETE", delete_endpoint)
                print(f"Service hook {sub_id} removed successfully.")

    def list_projects_with_tag_filter(self, target_tags):
        """
        Lists projects with specific tags in their descriptions.
        
        Args:
            target_tags (list): List of tags to filter projects by.
        """
        print("Fetching projects with tags:", target_tags)
        endpoint = f"_apis/projects?api-version={self.get_api_version('projects')}"
        response = self.handle_request("GET", endpoint)
        projects = response.get('value', [])

        filtered_projects = []
        for project in projects:
            description = project.get("description", "")
            try:
                match = re.search(r"\{.*\"tags\":.*\}", description)
                if match:
                    metadata = json.loads(match.group())
                    project_tags = metadata.get("tags", [])
                    if any(tag in project_tags for tag in target_tags):
                        filtered_projects.append(project)
            except (json.JSONDecodeError, AttributeError):
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

    def create_hooks_for_filtered_projects(self, target_tags, event_type, hook_url=None, state_changed=False):
        """
        Creates service hooks for projects that match the specified tags.
        
        Args:
            target_tags (list): List of tags to filter projects by.
            event_type (str): The event type for the service hook.
            hook_url (str, optional): The webhook URL. If not provided, uses default from config.
            state_changed (bool): If True, only trigger on state changes for workitem.updated.
        """
        print(f"Creating service hooks for projects with tags: {target_tags}")
        filtered_projects = self.list_projects_with_tag_filter(target_tags)
        
        if not filtered_projects:
            print("No projects found with the specified tags. No service hooks will be created.")
            return

        hook_url = hook_url or Config.get_webhook_url(event_type)
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
        print(f"Filtering projects by tags: {target_tags}")
        filtered_projects = self.list_projects_with_tag_filter(target_tags)

        if not filtered_projects:
            print("No projects matched the specified tags.")
            return

        for project in filtered_projects:
            project_id = project["id"]
            print(f"Upgrading webhooks for project: {project['name']} (ID: {project_id})")

            endpoint = f"_apis/hooks/subscriptions?publisherId=tfs&publisherInputFilters=projectId={project_id}&api-version={self.get_api_version('hooks')}"
            response = self.handle_request("GET", endpoint)
            subscriptions = response.get("value", [])

            if not subscriptions:
                print(f"No webhooks found for project {project['name']} (ID: {project_id}).")
                continue

            for sub in subscriptions:
                if sub.get("eventType") == "workitem.updated":
                    subscription_id = sub["id"]
                    sub["resourceVersion"] = "1.0"

                    update_endpoint = f"_apis/hooks/subscriptions/{subscription_id}?api-version={self.get_api_version('hooks')}"
                    self.handle_request("PUT", update_endpoint, sub)
                    print(f"Updated webhook {subscription_id} for project {project['name']} to resourceVersion: 1.0")

        print("All applicable webhooks have been updated.")

    def create_standard_hooks(self, project_id=None, target_tags=None):
        """
        Creates three standard service hooks for specified projects.

        Args:
            project_id (str, optional): The ID of a specific project.
            target_tags (list, optional): List of tags to filter projects by.
                                         Use at most one of these parameters.
                                         If neither is provided, uses STANDARD_HOOK_PROJECT_IDS from .env file.
        """
        # Get project IDs from all possible sources
        target_project_ids_from_env = Config.get_standard_hook_project_ids()
        
        print(f"Debug - IDs from .env: {target_project_ids_from_env}")
        print(f"Debug - Number of IDs: {len(target_project_ids_from_env)}")
        print(f"Debug - First few IDs: {target_project_ids_from_env[:3] if target_project_ids_from_env else 'None'}")
        
        # Check for conflicting parameters
        if project_id and target_tags:
            print("Error: Provide either --project-id or --filter-tag, not both.")
            return
            
        # Check if we have any source for project IDs
        if not project_id and not target_tags and not target_project_ids_from_env:
            print("Error: No target projects specified. Provide --project-id, --filter-tag, or set STANDARD_HOOK_PROJECT_IDS in .env file.")
            return
        
        # Warn if command line args override .env
        if (project_id or target_tags) and target_project_ids_from_env:
             print("Warning: --project-id or --filter-tag provided, ignoring STANDARD_HOOK_PROJECT_IDS from .env file.")

        standard_hooks = [
            {
                "event_type": "workitem.created",
                "hook_url": "https://prod-17.northcentralus.logic.azure.com:443/workflows/508aabfd2a114a949be865d9ace951b5/triggers/Se_crea_un_nuevo_work_item/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2FSe_crea_un_nuevo_work_item%2Frun&sv=1.0&sig=S2b_XQdlWwrHQqXk6VD9cPBpL_PFGumj03_eVPD7Eh0",
                "description": "Work Item Created (Standard)"
            },
            {
                "event_type": "workitem.updated",
                "hook_url": "https://prod-26.southcentralus.logic.azure.com:443/workflows/7a3968a93851401dabb3f01ba7d82ddf/triggers/Se_actualiza_un_work_item_asignado_o_se_reasigna_uno_existente/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2FSe_actualiza_un_work_item_asignado_o_se_reasigna_uno_existente%2Frun&sv=1.0&sig=2tiU0mGmHm-pDP1fKgZJz-TOBCXZcVkes7zlK87_zIM",
                "description": "Work Item Updated - Assigned/Reassigned (Standard)"
            },
            {
                "event_type": "workitem.updated",
                "hook_url": "https://prod-18.southcentralus.logic.azure.com:443/workflows/7e3259e5607740f28c50621158d7274e/triggers/Se_actualiza_el_estado_de_un_WI_y_notifica_al_creador/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2FSe_actualiza_el_estado_de_un_WI_y_notifica_al_creador%2Frun&sv=1.0&sig=Ygc6X0zNAqROkOCbBCKWGGmEXA_HVvoSvq9J0LYrUj8",
                "description": "Work Item Updated - State Change Notification (Standard)"
            }
        ]

        target_project_ids = []
        if project_id:
            # Validate project_id exists? Maybe not needed, API call will fail.
            target_project_ids.append(project_id)
            print(f"Targeting specific project ID: {project_id}")
        elif target_tags:
            print(f"Filtering projects by tags: {target_tags}")
            filtered_projects = self.list_projects_with_tag_filter(target_tags)
            if not filtered_projects:
                print("No projects matched the specified tags. No hooks will be created.")
                return
            target_project_ids = [p['id'] for p in filtered_projects]
        elif target_project_ids_from_env:
            print(f"Using project IDs from .env file: {target_project_ids_from_env}")
            target_project_ids = target_project_ids_from_env
        else:
            print("Error: No target projects specified. Provide --project-id, --filter-tag, or set STANDARD_HOOK_PROJECT_IDS in .env file.")
            return

        if not target_project_ids: # Add a check just in case
            print("Internal Error: Could not determine target project IDs.")
            return

        for pid in target_project_ids:
            print(f"--- Creating standard hooks for Project ID: {pid} ---")
            for hook_def in standard_hooks:
                print(f"  Creating hook: {hook_def['description']} ({hook_def['event_type']})")
                try:
                    # We pass state_changed=False as none of these standard hooks need it
                    self.create_service_hook(pid, hook_def['event_type'], hook_def['hook_url'], state_changed=False)
                except Exception as e:
                    print(f"  Error creating hook ({hook_def['description']}) for project {pid}: {e}")
            print(f"--- Finished standard hooks for Project ID: {pid} ---")

        print("Standard hook creation process completed.")

    def export_projects_to_csv(self, filename="projects_export.csv"):
        """
        Exports all projects (Name, ID, Tags) to a CSV file.

        Args:
            filename (str): The name of the CSV file to create.
        """
        print(f"Fetching all projects to export to {filename}...")
        endpoint = f"_apis/projects?api-version={self.get_api_version('projects')}"
        response = self.handle_request("GET", endpoint)
        projects = response.get('value', [])

        if not projects:
            print("No projects found to export.")
            return

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Project Name', 'Project ID', 'Tags']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                
                exported_count = 0
                for project in projects:
                    project_name = project['name']
                    project_id = project['id']
                    description = project.get("description", "")
                    tags = []
                    
                    # Extract tags using regex (similar to list_projects_with_tag_filter)
                    try:
                        match = re.search(r"\{.*\"tags\":.*\}", description)
                        if match:
                            metadata = json.loads(match.group())
                            tags = metadata.get("tags", [])
                    except (json.JSONDecodeError, AttributeError):
                        pass # Ignore if description doesn't contain valid tag JSON

                    writer.writerow({
                        'Project Name': project_name,
                        'Project ID': project_id,
                        'Tags': ", ".join(tags) # Join tags into a comma-separated string
                    })
                    exported_count += 1
            
            print(f"Successfully exported {exported_count} projects to {filename}")

        except IOError as e:
            print(f"Error writing to CSV file {filename}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during CSV export: {e}")


                
                    
            



