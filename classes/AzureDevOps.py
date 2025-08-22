import requests
import base64
import sys
from config.config import Config


class AzureDevOps:
    """
    A wrapper class for handling Azure DevOps credentials and common functions.
    """
    def __init__(self, organization=None, personal_access_token=None):
        self.organization = organization or Config.AZURE_DEVOPS_ORG
        self.pat = personal_access_token or Config.AZURE_DEVOPS_PAT
        self.encoded_pat = base64.b64encode(f":{self.pat}".encode()).decode()
        self.base_url = f"https://dev.azure.com/{self.organization}/"
        
        # Validate credentials
        if not self.organization or not self.pat:
            Config.validate_credentials()

    def handle_request(self, method, endpoint, data=None):
        """
        Handles HTTP requests with error handling.
        
        Args:
            method (str): HTTP method (GET, POST, PUT, DELETE)
            endpoint (str): API endpoint
            data (dict): Request data for POST/PUT methods
            
        Returns:
            dict: Response data
            
        Raises:
            requests.exceptions.HTTPError: If the request fails
            ValueError: If the response is not valid JSON
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Basic {self.encoded_pat}",
            "Content-Type": "application/json"
        }
        
        try:
            print(f"Sending {method} request to: {url}")
            response = requests.request(method, url, headers=headers, json=data)
            response.raise_for_status()
            
            # Handle empty responses
            if not response.content:
                return {}
                
            return response.json()
            
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            print(f"Response content: {response.content}")
            sys.exit(1)
        except ValueError as json_err:
            print(f"Invalid JSON response: {json_err}")
            print(f"Response content: {response.content}")
            sys.exit(1)
        except Exception as err:
            print(f"An unexpected error occurred: {err}")
            sys.exit(1)
            
    def get_api_version(self, service):
        """Get the API version for a specific service."""
        return Config.API_VERSION.get(service, "6.0")
