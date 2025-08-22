import requests
from classes.AzureDevOps import AzureDevOps


class AzureDevOpsProjectOperations(AzureDevOps):
    """
    A class for performing operations on a specific Azure DevOps project.
    """

    def __init__(self, organization, personal_access_token, project_id):
        super().__init__(organization, personal_access_token)
        self.project_id = project_id

    def list_work_items(self, filters=None):
        """
        List all work items for the specified project with optional filters.
        
        Args:
            filters (dict): Optional filters like "State", "Type", or "AssignedTo".
        """
        print(f"Fetching work items for project ID: {self.project_id}")

        # Step 1: Build WIQL Query
        query = "SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = @project"
        if filters:
            for key, value in filters.items():
                query += f" AND [System.{key}] = '{value}'"
        query_body = {"query": query}

        # Step 2: Execute Query to Get IDs
        wiql_endpoint = f"{self.project_id}/_apis/wit/wiql?api-version=7.1"
        try:
            response = self.handle_request("POST", wiql_endpoint, data=query_body)
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            return

        work_item_ids = [item['id'] for item in response.get("workItems", [])]
        if not work_item_ids:
            print("No work items found.")
            return

        print(f"Found {len(work_item_ids)} work items.")

        # Step 3: Fetch Details for Each Work Item
        chunk_size = 200  # Azure DevOps API allows a max of 200 IDs per request
        for i in range(0, len(work_item_ids), chunk_size):
            ids_chunk = work_item_ids[i:i + chunk_size]
            ids = ",".join(map(str, ids_chunk))
            work_items_endpoint = f"{self.project_id}/_apis/wit/workitems?ids={ids}&api-version=7.1"

            try:
                details_response = self.handle_request("GET", work_items_endpoint)
            except requests.exceptions.HTTPError as http_err:
                print(f"HTTP error occurred while fetching work item details: {http_err}")
                continue

            # Print work item details
            for item in details_response.get("value", []):
                fields = item.get("fields", {})
                print(f"Work Item ID: {item['id']}")
                print(f"Type: {fields.get('System.WorkItemType')}")
                print(f"Title: {fields.get('System.Title')}")
                print(f"State: {fields.get('System.State')}")
                print("-" * 40)

    def create_work_item(self, work_item_type, title, description=None, additional_fields=None):
        """
        Create a new work item in the project.

        Args:
            work_item_type (str): The type of work item (e.g., "Bug", "Task").
            title (str): The title of the work item.
            description (str): The description of the work item (optional).
            additional_fields (dict): Additional fields to set (optional).
        """
        print(f"Creating a new work item in project ID: {self.project_id}")
        endpoint = f"{self.project_id}/_apis/wit/workitems/${work_item_type}?api-version=7.1"
        headers = {
            "Content-Type": "application/json-patch+json"
        }

        data = [
            {"op": "add", "path": "/fields/System.Title", "value": title}
        ]
        if description:
            data.append({"op": "add", "path": "/fields/System.Description", "value": description})
        if additional_fields:
            for field, value in additional_fields.items():
                data.append({"op": "add", "path": f"/fields/{field}", "value": value})

        try:
            response = self.handle_request("POST", endpoint, data=data)
            print(f"Work item created successfully. ID: {response['id']}")
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")

    def list_github_repositories(self):
        """
        List GitHub repositories connected to the project.
        """
        print(f"Fetching GitHub repositories for project ID: {self.project_id}")
        endpoint = f"{self.project_id}/_apis/serviceendpoint/endpoints?type=github&api-version=7.1"

        try:
            response = self.handle_request("GET", endpoint)
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            return

        repositories = response.get('value', [])
        if repositories:
            for repo in repositories:
                print(f"Repository Name: {repo.get('name')}")
                print(f"URL: {repo.get('url')}")
                print("-" * 40)
        else:
            print("No GitHub repositories connected to this project.")

