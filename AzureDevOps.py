import requests
import base64
import sys


class AzureDevOps:
    """
    A wrapper class for handling Azure DevOps credentials and common functions.
    """
    def __init__(self, organization, personal_access_token):
        self.organization = organization
        self.pat = personal_access_token
        self.encoded_pat = base64.b64encode(f":{self.pat}".encode()).decode()
        self.base_url = f"https://dev.azure.com/{self.organization}/"

    def handle_request(self, method, endpoint, data=None):
        """
        Handles HTTP requests with error handling.
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
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            print(f"Response content: {response.content}")
            sys.exit(1)
        except Exception as err:
            print(f"An error occurred: {err}")
            sys.exit(1)
