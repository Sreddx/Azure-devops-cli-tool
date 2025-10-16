"""
Project discovery module for Azure DevOps work item operations.
Handles efficient discovery of projects with user activity.
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import quote


class ProjectDiscovery:
    """Handles discovering projects with user activity efficiently."""
    
    def __init__(self, azure_devops_client):
        """
        Initialize with Azure DevOps client.
        
        Args:
            azure_devops_client: Instance of AzureDevOps client for API calls
        """
        self.client = azure_devops_client
        self.projects_cache_file = "projects_cache.json"
    
    def find_projects_with_user_activity(self, 
                                        assigned_to: List[str], 
                                        work_item_types: Optional[List[str]] = None,
                                        states: Optional[List[str]] = None,
                                        start_date: Optional[str] = None,
                                        end_date: Optional[str] = None,
                                        date_field: str = "ClosedDate",
                                        max_projects: int = None) -> List[Dict]:
        """
        Find projects that have work item activity for specific users.
        
        Args:
            assigned_to: List of users to look for
            work_item_types: Work item types to filter by
            states: States to filter by
            start_date: Start date for filtering
            end_date: End date for filtering
            date_field: Field to use for date filtering
            max_projects: Maximum number of projects to check
            
        Returns:
            List of projects with user activity
        """
        print(f"Finding projects with activity for users: {', '.join(assigned_to)}")
        
        if not assigned_to:
            print("No users specified for filtering")
            return []
        
        # Build query conditions
        conditions = self._build_query_conditions(
            assigned_to, work_item_types, states, start_date, end_date, date_field
        )
        
        if not conditions:
            print("No valid query conditions built")
            return []
        
        # Use cached projects for efficiency
        print("Using smart project discovery with caching...")
        
        # Get projects from cache or API
        if max_projects:
            # Limited search - get first N projects
            project_endpoint = f"_apis/projects?$top={max_projects}&api-version={self.client.get_api_version('projects')}"
        else:
            # Get all projects using cache
            try:
                all_projects = self.get_all_projects_cached()
                print(f"Got {len(all_projects)} projects from cache/API")
                
                # Process all projects efficiently
                return self._test_projects_for_user_activity(all_projects, conditions)
            except Exception as e:
                print(f"Cache approach failed: {e}, falling back to API...")
                project_endpoint = f"_apis/projects?$top=200&api-version={self.client.get_api_version('projects')}"
        
        try:
            if max_projects:
                print(f"Fetching first {max_projects} projects only...")
            else:
                print("Fetching up to 200 projects...")
            
            response = self.client.handle_request("GET", project_endpoint)
            limited_projects = response.get('value', [])
            
            print(f"Got {len(limited_projects)} projects to check")
            
            # Use the helper method to test projects
            found_projects = self._test_projects_for_user_activity(limited_projects, conditions)
        
        except Exception as e:
            print(f"Error in project discovery: {e}")
            # Fallback to getting all projects if the targeted approach fails
            print("Falling back to cached project approach...")
            try:
                all_projects = self.get_all_projects_cached()
                found_projects = self._test_projects_for_user_activity(all_projects, conditions)
            except Exception as e2:
                print(f"Cache fallback also failed: {e2}")
                return []
        
        if found_projects:
            project_names = [p['name'] for p in found_projects]
            print(f"Found {len(found_projects)} projects with user activity: {', '.join(project_names)}")
        else:
            print("No projects found with the specified user activity")
            print("This might mean:")
            print("  - The users don't have work items in the specified date range")
            print("  - The users' work items are in projects not yet checked")
            print("  - Try increasing --max-projects to check more projects")
        
        return found_projects
    
    def _build_query_conditions(self, assigned_to: List[str], work_item_types: Optional[List[str]],
                               states: Optional[List[str]], start_date: Optional[str], 
                               end_date: Optional[str], date_field: str) -> List[str]:
        """Build WIQL query conditions for project discovery."""
        conditions = []
        
        # Users filter - this is our primary filter
        assigned_str = "', '".join(assigned_to)
        conditions.append(f"[System.AssignedTo] IN ('{assigned_str}')")
        
        # Work item types filter
        if work_item_types:
            types_str = "', '".join(work_item_types)
            conditions.append(f"[System.WorkItemType] IN ('{types_str}')")
        
        # States filter
        if states:
            states_str = "', '".join(states)
            conditions.append(f"[System.State] IN ('{states_str}')")
        
        # Date range filter
        field_mapping = {
            "ClosedDate": "Microsoft.VSTS.Common.ClosedDate",
            "StartDate": "Microsoft.VSTS.Scheduling.StartDate", 
            "TargetDate": "Microsoft.VSTS.Scheduling.TargetDate",
            "CreatedDate": "System.CreatedDate",
            "ChangedDate": "System.ChangedDate"
        }
        
        wiql_date_field = field_mapping.get(date_field, date_field)
        
        if start_date:
            conditions.append(f"[{wiql_date_field}] >= '{start_date}'")
        if end_date:
            conditions.append(f"[{wiql_date_field}] <= '{end_date}'")
        
        return conditions
    
    def _test_projects_for_user_activity(self, projects: List[Dict], conditions: List[str]) -> List[Dict]:
        """
        Test a list of projects for user activity efficiently.
        
        Args:
            projects: List of project dictionaries
            conditions: WIQL query conditions to test
            
        Returns:
            List of projects with user activity
        """
        found_projects = []
        
        # Process in batches for better performance
        batch_size = 20
        for batch_start in range(0, len(projects), batch_size):
            batch_end = min(batch_start + batch_size, len(projects))
            batch_projects = projects[batch_start:batch_end]
            
            print(f"  Processing projects {batch_start + 1}-{batch_end} of {len(projects)}...")
            
            for project in batch_projects:
                try:
                    if not conditions:
                        print(f"    ✗ {project['name']} - No conditions to test")
                        continue
                    
                    test_query = f"""SELECT [System.Id]
                                   FROM WorkItems 
                                   WHERE {' AND '.join(conditions)}"""
                    
                    endpoint = f"{project['id']}/_apis/wit/wiql?api-version={self.client.get_api_version('wiql')}"
                    data = {"query": test_query}
                    response = self.client.handle_request("POST", endpoint, data)
                    work_items = response.get("workItems", [])
                    
                    if work_items:
                        found_projects.append(project)
                        print(f"    ✓ {project['name']} - Found user activity ({len(work_items)} items)")
                    else:
                        print(f"    - {project['name']} - No matching work items")
                    
                except Exception as e:
                    # Skip projects that error out (likely permission issues)
                    print(f"    ✗ {project['name']} - Skipped: {str(e)[:50]}...")
                    continue
        
        return found_projects
    
    def get_all_projects_cached(self, refresh_cache: bool = False) -> List[Dict]:
        """
        Get all projects with caching support to avoid repeated API calls.
        
        Args:
            refresh_cache: If True, fetch fresh data from API and update cache
            
        Returns:
            List of project dictionaries with id, name, and description
        """
        cache_file_path = os.path.join(os.path.dirname(__file__), self.projects_cache_file)
        
        # Check if we should use cached data
        if not refresh_cache and os.path.exists(cache_file_path):
            try:
                with open(cache_file_path, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                # Check if cache is recent (less than 24 hours old)
                cache_age = datetime.now() - datetime.fromisoformat(cached_data.get('timestamp', '2000-01-01'))
                if cache_age.total_seconds() < 86400:  # 24 hours
                    print(f"Using cached projects data ({len(cached_data['projects'])} projects, age: {cache_age})")
                    return cached_data['projects']
                else:
                    print("Cached projects data is older than 24 hours, refreshing...")
            except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
                print(f"Cache file invalid or not found: {e}, fetching fresh data...")
        
        # Fetch fresh data from API
        print("Fetching all projects from Azure DevOps API...")
        projects = self.get_all_projects()
        
        # Save to cache
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'organization': self.client.organization,
                'project_count': len(projects),
                'projects': projects
            }
            
            with open(cache_file_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            print(f"Cached {len(projects)} projects to {cache_file_path}")
            
        except Exception as e:
            print(f"Warning: Could not save projects cache: {e}")
        
        return projects
    
    def get_all_projects(self) -> List[Dict]:
        """
        Get all projects in the organization.
        
        Returns:
            List of project dictionaries with id, name, and description
        """
        print("Fetching all projects in the organization...")
        endpoint = f"_apis/projects?api-version={self.client.get_api_version('projects')}"
        response = self.client.handle_request("GET", endpoint)
        projects = response.get('value', [])
        
        simplified_projects = []
        for project in projects:
            simplified_projects.append({
                'id': project['id'],
                'name': project['name'],
                'description': project.get('description', ''),
                'url': project.get('url', '')
            })
        
        print(f"Found {len(simplified_projects)} projects")
        return simplified_projects
    
    def filter_projects_by_name(self, projects: List[Dict], project_names: List[str]) -> List[Dict]:
        """
        Filter projects by name.
        
        Args:
            projects: List of all projects
            project_names: List of project names to filter by
            
        Returns:
            Filtered list of projects
        """
        if not project_names:
            return projects
        
        filtered = []
        for project in projects:
            if project['name'] in project_names:
                filtered.append(project)
        
        if not filtered:
            print(f"Warning: No projects found matching names: {project_names}")
        else:
            print(f"Filtered to {len(filtered)} projects: {[p['name'] for p in filtered]}")
        
        return filtered