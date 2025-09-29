"""
Simple Logic App helper for fetching estimated hours from Fabric Data Warehouse.
Sends work item IDs in the exact format: {"work_item_ids": []}
"""

import requests
import logging
from typing import List, Dict, Any


class FabricLogicAppHelper:
    """Simple helper for calling Logic App endpoint to fetch estimated hours."""

    def __init__(self, logic_app_url: str):
        """
        Initialize with Logic App URL.

        Args:
            logic_app_url: The HTTP trigger URL of your Azure Logic App
        """
        self.logic_app_url = logic_app_url
        self.logger = logging.getLogger(__name__)

    def get_estimated_hours_by_ids(self, work_item_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get work items with estimated hours from Logic App.

        Args:
            work_item_ids: List of work item IDs to fetch

        Returns:
            List of work item dictionaries with estimated hours
        """
        if not work_item_ids:
            return []

        try:
            # Simple payload in exact format requested
            payload = {
                "work_item_ids": work_item_ids
            }

            self.logger.info(f"Requesting estimated hours for {len(work_item_ids)} work items")

            # Call Logic App
            response = requests.post(
                self.logic_app_url,
                json=payload,
                headers={
                    'Content-Type': 'application/json'
                },
                timeout=60
            )

            response.raise_for_status()
            result = response.json()

            self.logger.info(f"Received response from Logic App")
            return result

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Logic App request failed: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error getting estimated hours: {e}")
            return []


def create_fabric_helper(logic_app_url: str) -> FabricLogicAppHelper:
    """
    Create configured FabricLogicAppHelper.

    Args:
        logic_app_url: Your Logic App HTTP trigger URL

    Returns:
        Configured helper instance
    """
    return FabricLogicAppHelper(logic_app_url)


# Example usage
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)

    # Replace with your actual Logic App URL
    LOGIC_APP_URL = "https://prod-10.northcentralus.logic.azure.com:443/workflows/9e4bccaa8aab448083f7b95d55db8660/triggers/When_an_HTTP_request_is_received/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2FWhen_an_HTTP_request_is_received%2Frun&sv=1.0&sig=PgB2Drl6tRQ7Ki418LzCop5QV3wtpVhpVBoiW3I2mS4"

    helper = create_fabric_helper(LOGIC_APP_URL)

    # Test with work item IDs from command line arguments
    if len(sys.argv) > 1:
        test_work_item_ids = sys.argv[1:]
        print(f"Testing with work item IDs: {test_work_item_ids}")
        work_items = helper.get_estimated_hours_by_ids(test_work_item_ids)
        print(f"Retrieved work items: {work_items}")
    else:
        print("Usage: python fabric_logic_app_helper.py <work_item_id1> <work_item_id2> ...")
        print("Example: python fabric_logic_app_helper.py 42964 42965 42966")