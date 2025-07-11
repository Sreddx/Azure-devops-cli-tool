from AzureDevOps import AzureDevOps
from datetime import datetime, timedelta
import json
from typing import List, Dict, Optional, Any
import csv
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from azure.devops.v7_1.work_item_tracking.models import Wiql
from urllib.parse import quote


class WorkItemOperations(AzureDevOps):
    """
    A class for handling work item querying and KPI calculations.
    """
    
    def __init__(self, organization=None, personal_access_token=None):
        super().__init__(organization, personal_access_token)
        
        # Initialize Azure DevOps SDK connection
        self.connection = None
        self.wit_client = None
        self._initialize_sdk_connection()
    
    def _initialize_sdk_connection(self):
        """Initialize Azure DevOps SDK connection."""
        try:
            organization_url = f"https://dev.azure.com/{self.organization}"
            credentials = BasicAuthentication('', self.pat)
            self.connection = Connection(base_url=organization_url, creds=credentials)
            self.wit_client = self.connection.clients.get_work_item_tracking_client()
            print("SDK connection initialized successfully")
        except Exception as e:
            print(f"Failed to initialize SDK connection: {e}")
            print("Will fallback to REST API calls")
    
    def get_all_projects(self) -> List[Dict]:
        """
        Get all projects in the organization.
        
        Returns:
            List of project dictionaries with id, name, and description
        """
        print("Fetching all projects in the organization...")
        endpoint = f"_apis/projects?api-version={self.get_api_version('projects')}"
        response = self.handle_request("GET", endpoint)
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
    
    def find_projects_with_user_activity_sdk(self,
                                           assigned_to: List[str], 
                                           work_item_types: Optional[List[str]] = None,
                                           states: Optional[List[str]] = None,
                                           start_date: Optional[str] = None,
                                           end_date: Optional[str] = None,
                                           date_field: str = "ClosedDate",
                                           max_projects: int = 50) -> List[Dict]:
        """
        Find projects with user activity using Azure DevOps SDK.
        Much more efficient than WIQL queries.
        
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
        # For now, use the REST API approach which is working well
        # The SDK approach had parameter issues, so we fall back to REST API
        print("Using REST API approach for project discovery")
        return self.find_projects_with_user_activity(
            assigned_to, work_item_types, states, start_date, end_date, date_field, max_projects
        )
    
    def find_projects_with_user_activity(self, 
                                        assigned_to: List[str], 
                                        work_item_types: Optional[List[str]] = None,
                                        states: Optional[List[str]] = None,
                                        start_date: Optional[str] = None,
                                        end_date: Optional[str] = None,
                                        date_field: str = "ClosedDate",
                                        max_projects: int = 50) -> List[Dict]:
        """
        Find projects that have work item activity for specific users.
        Uses a completely different approach that doesn't fetch all projects.
        
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
        
        if not conditions:
            print("No valid query conditions built")
            return []
        
        # NEW STRATEGY: Instead of fetching all projects, use a more targeted approach
        # This approach queries a limited set of projects that are most likely to have user activity
        
        print(f"Using efficient project discovery (checking up to {max_projects} projects)...")
        
        # COMPLETELY NEW APPROACH: Don't fetch all projects!
        # Instead, let's use a targeted discovery method
        
        found_projects = []
        
        # Strategy 1: Try to use project names from common patterns or heuristics
        # This is much more efficient than fetching all projects
        
        print("Using smart project discovery...")
        
        # First, try to query a few well-known or recently active projects
        # Get minimal project info without fetching all
        project_endpoint = f"_apis/projects?$top={max_projects}&api-version={self.get_api_version('projects')}"
        
        try:
            print(f"Fetching first {max_projects} projects only...")
            response = self.handle_request("GET", project_endpoint)
            limited_projects = response.get('value', [])
            
            print(f"Got {len(limited_projects)} projects to check")
            
            # Process in smaller batches
            batch_size = 10
            for batch_start in range(0, len(limited_projects), batch_size):
                batch_end = min(batch_start + batch_size, len(limited_projects))
                batch_projects = limited_projects[batch_start:batch_end]
                
                print(f"  Processing projects {batch_start + 1}-{batch_end} of {len(limited_projects)}...")
                
                for project in batch_projects:
                    try:
                        # Quick existence check with minimal query
                        # Debug: Print the conditions to see what's wrong
                        print(f"    Testing conditions: {conditions}")
                        
                        if not conditions:
                            print(f"    ✗ {project['name']} - No conditions to test")
                            continue
                        
                        test_query = f"""SELECT [System.Id]
                                       FROM WorkItems 
                                       WHERE {' AND '.join(conditions)}"""
                        
                        print(f"    Query: {test_query}")
                        
                        endpoint = f"{project['id']}/_apis/wit/wiql?api-version={self.get_api_version('wiql')}"
                        data = {"query": test_query}
                        response = self.handle_request("POST", endpoint, data)
                        work_items = response.get("workItems", [])
                        
                        if work_items:
                            # Convert to our expected format
                            project_info = {
                                'id': project['id'],
                                'name': project['name'],
                                'description': project.get('description', ''),
                                'url': project.get('url', '')
                            }
                            found_projects.append(project_info)
                            print(f"    ✓ {project['name']} - Found user activity")
                        else:
                            print(f"    - {project['name']} - No matching work items")
                        
                    except Exception as e:
                        # Skip projects that error out (likely permission issues)
                        print(f"    ✗ {project['name']} - Skipped: {str(e)[:50]}...")
                        continue
        
        except Exception as e:
            print(f"Error in project discovery: {e}")
            # Fallback to getting all projects if the targeted approach fails
            print("Falling back to full project list...")
            all_projects = self.get_all_projects()
            target_projects = all_projects[:max_projects]
            
            for project in target_projects:
                try:
                    test_query = f"""SELECT [System.Id]
                                   FROM WorkItems 
                                   WHERE {' AND '.join(conditions)}"""
                    
                    endpoint = f"{project['id']}/_apis/wit/wiql?api-version={self.get_api_version('wiql')}"
                    data = {"query": test_query}
                    response = self.handle_request("POST", endpoint, data)
                    work_items = response.get("workItems", [])
                    
                    if work_items:
                        found_projects.append(project)
                        print(f"    ✓ {project['name']} - Found user activity")
                    
                except Exception as e:
                    continue
        
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
        
    def build_wiql_query(self, 
                        assigned_to: Optional[List[str]] = None,
                        work_item_types: Optional[List[str]] = None,
                        states: Optional[List[str]] = None,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None,
                        date_field: str = "ClosedDate",
                        additional_filters: Optional[Dict[str, str]] = None) -> str:
        """
        Build a dynamic WIQL query based on provided parameters.
        
        Args:
            assigned_to: List of users to filter by
            work_item_types: List of work item types to include
            states: List of states to filter by
            start_date: Start date for filtering (YYYY-MM-DD format)
            end_date: End date for filtering (YYYY-MM-DD format)
            date_field: Field to use for date filtering
            additional_filters: Additional filters (area_path, iteration_path, etc.) (optional)
            
        Returns:
            str: WIQL query string
        """
        query = """SELECT [System.Id], [System.Title], [System.AssignedTo], [System.State],
                   [System.WorkItemType], [System.CreatedDate], [System.ChangedDate],
                   [Microsoft.VSTS.Scheduling.StartDate], 
                   [Microsoft.VSTS.Scheduling.TargetDate],
                   [Microsoft.VSTS.Common.ClosedDate],
                   [System.AreaPath], [System.IterationPath]
                   FROM WorkItems WHERE """
        
        conditions = []
        
        # Work item types filter
        if work_item_types:
            types_str = "', '".join(work_item_types)
            conditions.append(f"[System.WorkItemType] IN ('{types_str}')")
        
        # Assigned to filter
        if assigned_to:
            assigned_str = "', '".join(assigned_to)
            conditions.append(f"[System.AssignedTo] IN ('{assigned_str}')")
        
        # States filter
        if states:
            states_str = "', '".join(states)
            conditions.append(f"[System.State] IN ('{states_str}')")
        
        # Date range filter - map field names to proper WIQL format
        field_mapping = {
            "ClosedDate": "Microsoft.VSTS.Common.ClosedDate",
            "StartDate": "Microsoft.VSTS.Scheduling.StartDate", 
            "TargetDate": "Microsoft.VSTS.Scheduling.TargetDate",
            "CreatedDate": "System.CreatedDate",
            "ChangedDate": "System.ChangedDate"
        }
        
        # Use mapped field name if available, otherwise use as-is
        wiql_date_field = field_mapping.get(date_field, date_field)
        
        if start_date:
            conditions.append(f"[{wiql_date_field}] >= '{start_date}'")
        if end_date:
            conditions.append(f"[{wiql_date_field}] <= '{end_date}'")
        
        # Additional filters
        if additional_filters:
            for field, value in additional_filters.items():
                if field == "area_path":
                    conditions.append(f"[System.AreaPath] UNDER '{value}'")
                elif field == "iteration_path":
                    conditions.append(f"[System.IterationPath] UNDER '{value}'")
                else:
                    conditions.append(f"[{field}] = '{value}'")
        
        if not conditions:
            conditions.append("1=1")  # Default condition if no filters provided
        
        query += " AND ".join(conditions)
        query += " ORDER BY [System.Id]"
        
        return query
    
    def execute_wiql_query(self, project_id: str, query: str) -> List[int]:
        """
        Execute a WIQL query and return work item IDs.
        
        Args:
            project_id: Project ID to query
            query: WIQL query string
            
        Returns:
            List of work item IDs
        """
        print(f"Executing WIQL query for project: {project_id}")
        endpoint = f"{project_id}/_apis/wit/wiql?api-version={self.get_api_version('wiql')}"
        
        data = {"query": query}
        response = self.handle_request("POST", endpoint, data)
        
        work_items = response.get("workItems", [])
        work_item_ids = [wi["id"] for wi in work_items]
        
        print(f"Found {len(work_item_ids)} work items")
        return work_item_ids
    
    def _get_project_url_segment(self, project_id, project_name):
        """
        Utility to get the correct project segment for API URLs, preferring ID, else URL-encoded name.
        """
        if project_id and project_id != "Unknown":
            return project_id
        elif project_name and project_name != "Unknown":
            return quote(project_name.strip(), safe='')
        else:
            raise ValueError("No valid project identifier available")

    def get_work_item_details(self, project_id: str, work_item_ids: List[int], project_name: str = None) -> List[Dict]:
        """
        Get detailed information for work items.
        Args:
            project_id: Project ID
            work_item_ids: List of work item IDs
            project_name: Project name (optional, for fallback)
        Returns:
            List of work item details
        """
        if not work_item_ids:
            return []
        print(f"Fetching details for {len(work_item_ids)} work items")
        ids_str = ",".join(map(str, work_item_ids))
        project_segment = self._get_project_url_segment(project_id, project_name)
        endpoint = f"{project_segment}/_apis/wit/workitems?ids={ids_str}&api-version={self.get_api_version('work_items')}"
        response = self.handle_request("GET", endpoint)
        work_items = response.get("value", [])
        # Transform to simpler format
        simplified_items = []
        for wi in work_items:
            fields = wi.get("fields", {})
            simplified_item = {
                "id": wi["id"],
                "title": fields.get("System.Title", ""),
                "assigned_to": fields.get("System.AssignedTo", {}).get("displayName", "Unassigned"),
                "state": fields.get("System.State", ""),
                "work_item_type": fields.get("System.WorkItemType", ""),
                "created_date": fields.get("System.CreatedDate", ""),
                "changed_date": fields.get("System.ChangedDate", ""),
                "start_date": fields.get("Microsoft.VSTS.Scheduling.StartDate", ""),
                "target_date": fields.get("Microsoft.VSTS.Scheduling.TargetDate", ""),
                "closed_date": fields.get("Microsoft.VSTS.Common.ClosedDate", ""),
                "area_path": fields.get("System.AreaPath", ""),
                "iteration_path": fields.get("System.IterationPath", "")
            }
            simplified_items.append(simplified_item)
        return simplified_items

    def get_work_item_revisions(self, project_id: str, work_item_id: int, project_name: str = None) -> List[Dict]:
        """
        Get revision history for a work item.
        Args:
            project_id: Project ID
            work_item_id: Work item ID
            project_name: Project name (optional, for fallback)
        Returns:
            List of revisions with state and date information
        """
        project_segment = self._get_project_url_segment(project_id, project_name)
        endpoint = f"{project_segment}/_apis/wit/workitems/{work_item_id}/revisions?api-version={self.get_api_version('work_items')}"
        response = self.handle_request("GET", endpoint)
        revisions = response.get("value", [])
        # Transform revisions to simpler format
        simplified_revisions = []
        for revision in revisions:
            fields = revision.get("fields", {})
            simplified_revision = {
                "revision": revision.get("rev", 0),
                "state": fields.get("System.State", ""),
                "changed_date": fields.get("System.ChangedDate", ""),
                "changed_by": fields.get("System.ChangedBy", {}).get("displayName", "Unknown"),
                "reason": fields.get("System.Reason", "")
            }
            simplified_revisions.append(simplified_revision)
        return simplified_revisions

    def calculate_active_time_efficiency(self, 
                                       state_history: List[Dict], 
                                       productive_states: Optional[List[str]] = None,
                                       blocked_states: Optional[List[str]] = None) -> Dict:
        """
        Calculate time efficiency metrics from state history.
        Args:
            state_history: List of state changes with timestamps
            productive_states: List of states considered productive (optional)
            blocked_states: List of states considered blocked (optional)
        Returns:
            Dictionary with efficiency metrics
        """
        if len(state_history) < 2:
            return {
                "active_time_hours": 0,
                "blocked_time_hours": 0,
                "total_time_hours": 0,
                "efficiency_percentage": 0,
                "state_breakdown": {}
            }
        active_time = timedelta()
        blocked_time = timedelta()
        total_time = timedelta()
        state_breakdown = {}
        for i in range(len(state_history) - 1):
            current_state = state_history[i]['state']
            next_change = datetime.fromisoformat(state_history[i+1]['changed_date'].replace('Z', '+00:00'))
            current_change = datetime.fromisoformat(state_history[i]['changed_date'].replace('Z', '+00:00'))
            time_in_state = next_change - current_change
            total_time += time_in_state
            # Track time per state
            if current_state not in state_breakdown:
                state_breakdown[current_state] = timedelta()
            state_breakdown[current_state] += time_in_state
            # Categorize time
            if productive_states is not None and current_state in productive_states:
                active_time += time_in_state
            elif blocked_states is not None and current_state in blocked_states:
                blocked_time += time_in_state
        # Convert to hours and calculate efficiency
        active_hours = active_time.total_seconds() / 3600
        blocked_hours = blocked_time.total_seconds() / 3600
        total_hours = total_time.total_seconds() / 3600
        efficiency = (active_hours / total_hours) * 100 if total_hours > 0 else 0
        # Convert state breakdown to hours
        state_breakdown_hours = {
            state: td.total_seconds() / 3600 
            for state, td in state_breakdown.items()
        }
        return {
            "active_time_hours": round(active_hours, 2),
            "blocked_time_hours": round(blocked_hours, 2),
            "total_time_hours": round(total_hours, 2),
            "efficiency_percentage": round(efficiency, 2),
            "state_breakdown": state_breakdown_hours
        }
    
    def calculate_comprehensive_kpi(self, work_items: List[Dict]) -> Dict:
        """
        Calculate comprehensive KPIs for a set of work items.
        Args:
            work_items: List of work items with efficiency data
        Returns:
            Dictionary with comprehensive KPI metrics
        """
        if not work_items:
            return {
                "total_work_items": 0,
                "on_time_delivery_percentage": 0,
                "average_efficiency_percentage": 0,
                "total_active_hours": 0,
                "total_blocked_hours": 0,
                "bottlenecks": [],
                "average_time_to_close_days": 0
            }
        total_items = len(work_items)
        on_time_count = 0
        total_efficiency = 0
        total_active_hours = 0
        total_blocked_hours = 0
        state_occurrences = {}
        total_time_to_close = 0
        closed_items_count = 0
        for item in work_items:
            # On-time delivery check
            if item.get("target_date") and item.get("closed_date"):
                try:
                    target = datetime.fromisoformat(item["target_date"].replace('Z', '+00:00'))
                    closed = datetime.fromisoformat(item["closed_date"].replace('Z', '+00:00'))
                    if closed <= target:
                        on_time_count += 1
                except:
                    pass  # Skip invalid dates
            # Efficiency aggregation
            efficiency_data = item.get("efficiency", {})
            if efficiency_data:
                total_efficiency += efficiency_data.get("efficiency_percentage", 0)
                total_active_hours += efficiency_data.get("active_time_hours", 0)
                total_blocked_hours += efficiency_data.get("blocked_time_hours", 0)
                # Track state occurrences for bottleneck analysis
                for state, hours in efficiency_data.get("state_breakdown", {}).items():
                    if state not in state_occurrences:
                        state_occurrences[state] = {"count": 0, "total_hours": 0}
                    state_occurrences[state]["count"] += 1
                    state_occurrences[state]["total_hours"] += hours
            # Time to close calculation (use start_date, not created_date)
            if item.get("start_date") and item.get("closed_date"):
                try:
                    start = datetime.fromisoformat(item["start_date"].replace('Z', '+00:00'))
                    closed = datetime.fromisoformat(item["closed_date"].replace('Z', '+00:00'))
                    days_to_close = (closed - start).total_seconds() / 86400
                    total_time_to_close += days_to_close
                    closed_items_count += 1
                except:
                    pass
        # Calculate averages
        on_time_percentage = (on_time_count / total_items) * 100 if total_items > 0 else 0
        avg_efficiency = total_efficiency / total_items if total_items > 0 else 0
        avg_time_to_close = total_time_to_close / closed_items_count if closed_items_count > 0 else 0
        # Identify bottlenecks (states with highest average time)
        bottlenecks = []
        for state, data in state_occurrences.items():
            avg_time = data["total_hours"] / data["count"] if data["count"] > 0 else 0
            bottlenecks.append({
                "state": state,
                "average_time_hours": round(avg_time, 2),
                "occurrences": data["count"]
            })
        # Sort by average time descending
        bottlenecks.sort(key=lambda x: x["average_time_hours"], reverse=True)
        return {
            "total_work_items": total_items,
            "on_time_delivery_percentage": round(on_time_percentage, 2),
            "average_efficiency_percentage": round(avg_efficiency, 2),
            "total_active_hours": round(total_active_hours, 2),
            "total_blocked_hours": round(total_blocked_hours, 2),
            "bottlenecks": bottlenecks[:5],  # Top 5 bottlenecks
            "average_time_to_close_days": round(avg_time_to_close, 2)
        }
    
    def execute_organization_wiql_query(self, 
                                       query: str, 
                                       target_projects: Optional[List[Dict]] = None,
                                       project_names: Optional[List[str]] = None) -> List[Dict]:
        print("Executing organization-level WIQL query...")
        endpoint = f"_apis/wit/wiql?api-version={self.get_api_version('wiql')}"
        if target_projects and len(target_projects) < 20:
            project_ids = [p['id'] for p in target_projects]
            project_filter = "', '".join(project_ids)
            if "WHERE" in query.upper():
                query = query.replace("WHERE", f"WHERE [System.TeamProjectId] IN ('{project_filter}') AND")
            else:
                query = query.replace("FROM WorkItems", f"FROM WorkItems WHERE [System.TeamProjectId] IN ('{project_filter}')")
        print(f"Organization query: {query}")
        data = {"query": query}
        response = self.handle_request("POST", endpoint, data)
        work_items = response.get("workItems", [])
        if not work_items:
            return []
        print(f"Found {len(work_items)} work items, fetching details...")
        all_work_items = []
        batch_size = 200
        # Build a mapping from project id and name to project info for later use
        project_id_to_name = {}
        project_name_to_id = {}
        if target_projects:
            for proj in target_projects:
                project_id_to_name[proj['id']] = proj['name']
                project_name_to_id[proj['name'].strip()] = proj['id']
        for i in range(0, len(work_items), batch_size):
            batch = work_items[i:i + batch_size]
            ids = [str(item['id']) for item in batch]
            ids_str = ",".join(ids)
            # Use organization-level work items endpoint
            details_endpoint = f"_apis/wit/workitems?ids={ids_str}&api-version={self.get_api_version('work_items')}"
            details_response = self.handle_request("GET", details_endpoint)
            batch_items = details_response.get("value", [])
            for wi in batch_items:
                fields = wi.get("fields", {})
                # Try to get project id, else resolve from project name
                project_id = fields.get("System.TeamProjectId")
                project_name = fields.get("System.TeamProject", "Unknown")
                if not project_id and project_name != "Unknown" and project_name_to_id:
                    # Strict match: strip and case-sensitive
                    project_id = project_name_to_id.get(project_name.strip())
                simplified_item = {
                    "id": wi["id"],
                    "title": fields.get("System.Title", ""),
                    "assigned_to": fields.get("System.AssignedTo", {}).get("displayName", "Unassigned"),
                    "state": fields.get("System.State", ""),
                    "work_item_type": fields.get("System.WorkItemType", ""),
                    "created_date": fields.get("System.CreatedDate", ""),
                    "changed_date": fields.get("System.ChangedDate", ""),
                    "start_date": fields.get("Microsoft.VSTS.Scheduling.StartDate", ""),
                    "target_date": fields.get("Microsoft.VSTS.Scheduling.TargetDate", ""),
                    "closed_date": fields.get("Microsoft.VSTS.Common.ClosedDate", ""),
                    "area_path": fields.get("System.AreaPath", ""),
                    "iteration_path": fields.get("System.IterationPath", ""),
                    "project_id": project_id if project_id else "Unknown",
                    "project_name": project_name
                }
                all_work_items.append(simplified_item)
        return all_work_items

    def find_projects_with_user_activity_audit_log(self,
                                                  assigned_to: List[str],
                                                  start_date: Optional[str] = None,
                                                  end_date: Optional[str] = None,
                                                  max_projects: int = 100) -> List[Dict]:
        """
        Find projects with user activity using Azure DevOps Audit Log API.
        This is the most efficient method for discovering user activity.
        
        Args:
            assigned_to: List of user emails/UPNs to look for
            start_date: Start date for audit log query (YYYY-MM-DD format)
            end_date: End date for audit log query (YYYY-MM-DD format)
            max_projects: Maximum number of projects to return
            
        Returns:
            List of projects with user activity
        """
        print(f"Using Audit Log API to find projects with activity for: {', '.join(assigned_to)}")
        
        # Format dates for audit log API (ISO 8601 format)
        if start_date:
            start_time = f"{start_date}T00:00:00Z"
        else:
            # Default to 30 days ago
            start_time = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        if end_date:
            end_time = f"{end_date}T23:59:59Z"
        else:
            end_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        projects_with_activity = set()
        
        # Query audit log for each user
        for user in assigned_to:
            try:
                print(f"  Querying audit log for user: {user}")
                
                # Build audit log query
                audit_endpoint = f"https://auditservice.dev.azure.com/{self.organization}/_apis/audit/auditlog"
                params = {
                    "startTime": start_time,
                    "endTime": end_time,
                    "actorUPN": user,
                    "api-version": "7.1-preview.1",
                    "batchSize": 1000  # Get more results per request
                }
                
                # Use custom request handling for audit service
                headers = {
                    "Authorization": f"Basic {self.encoded_pat}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                
                import requests
                
                # Make the request with proper error handling
                response = requests.get(audit_endpoint, params=params, headers=headers)
                print(response)
                if response.status_code == 200:
                    audit_data = response.json()
                    entries = audit_data.get("decoratedAuditLogEntries", [])
                    
                    print(f"    Found {len(entries)} audit log entries for {user}")
                    
                    # Extract project names from audit entries
                    for entry in entries:
                        project_name = entry.get("projectName")
                        if project_name and project_name != "Unknown":
                            projects_with_activity.add(project_name)
                            
                elif response.status_code == 403:
                    print(f"    WARNING: Access denied to audit log for {user}")
                    print("    This might mean:")
                    print("    - Audit logging is not enabled for this organization")
                    print("    - Your PAT doesn't have 'vso.auditlog' scope")
                    print("    - Organization is not backed by Microsoft Entra ID")
                    print("    Falling back to previous method...")
                    return self.find_projects_with_user_activity_sdk(
                        assigned_to=assigned_to,
                        max_projects=max_projects
                    )
                else:
                    print(f"    ERROR: Audit log query failed with status {response.status_code}")
                    print(f"    Response: {response.text[:200]}...")
                    
            except Exception as e:
                print(f"    ERROR querying audit log for {user}: {e}")
                continue
        
        # Convert project names to project objects
        if projects_with_activity:
            print(f"Found user activity in {len(projects_with_activity)} projects from audit log")
            
            # Get full project details for the projects with activity
            target_projects = []
            all_projects = self.get_all_projects()
            
            for project in all_projects:
                if project['name'] in projects_with_activity:
                    target_projects.append(project)
                    
                # Respect max_projects limit
                if len(target_projects) >= max_projects:
                    break
            
            project_names = [p['name'] for p in target_projects]
            project_ids = [p['id'] for p in target_projects]
            print(f"Audit log-based project discovery found: {', '.join(project_ids)}")
            
            return target_projects
        else:
            print("No projects found with user activity in audit log")
            return []

    def get_work_items_with_efficiency(self,
                                     project_id: Optional[str] = None,
                                     project_names: Optional[List[str]] = None,
                                     assigned_to: Optional[List[str]] = None,
                                     work_item_types: Optional[List[str]] = None,
                                     states: Optional[List[str]] = None,
                                     start_date: Optional[str] = None,
                                     end_date: Optional[str] = None,
                                     date_field: str = "ClosedDate",
                                     additional_filters: Optional[Dict[str, str]] = None,
                                     calculate_efficiency: bool = True,
                                     productive_states: Optional[List[str]] = None,
                                     blocked_states: Optional[List[str]] = None,
                                     all_projects: bool = False,
                                     max_projects: int = 50) -> Dict:
        """
        Main method to get work items with efficiency calculations.
        
        Args:
            project_id: Single project ID to query (optional)
            project_names: List of project names to filter by (optional)
            assigned_to: List of users to filter by
            work_item_types: List of work item types
            states: List of states to filter by
            start_date: Start date for filtering
            end_date: End date for filtering
            date_field: Field to use for date filtering
            additional_filters: Additional filters (optional)
            calculate_efficiency: Whether to calculate efficiency metrics
            productive_states: States considered productive (optional)
            blocked_states: States considered blocked (optional)
            
        Returns:
            Dictionary with work items and KPIs
        """
        # Default values
        if work_item_types is None:
            work_item_types = ["Task", "User Story", "Bug"]
        if states is None:
            states = ["Closed", "Done", "Resolved"]
        # Do not set defaults for productive_states, blocked_states, or additional_filters
        # Determine which projects to query
        if project_id:
            # Single project query
            target_projects = [{'id': project_id, 'name': f'Project {project_id}'}]
        else:
            # Multi-project query
            if project_names:
                # Query specific projects by name
                all_projects = self.get_all_projects()
                target_projects = self.filter_projects_by_name(all_projects, project_names)
            elif assigned_to and not all_projects:
                # Smart filtering: use audit log for most efficient project discovery
                print("Using audit log-based project discovery for optimal performance...")
                target_projects = self.find_projects_with_user_activity_audit_log(
                    assigned_to=assigned_to,
                    start_date=start_date,
                    end_date=end_date,
                    max_projects=max_projects
                )
            else:
                # No users specified or all_projects flag is set, query all projects
                print("WARNING: Querying all projects without user filtering may be slow")
                target_projects = self.get_all_projects()
        if not target_projects:
            print("No projects found to query.")
            return {
                "work_items": [],
                "kpis": self.calculate_comprehensive_kpi([]),
                "query_info": {
                    "total_items": 0,
                    "projects_queried": [],
                    "filters_applied": {}
                }
            }
        # Build query
        query = self.build_wiql_query(
            assigned_to=assigned_to,
            work_item_types=work_item_types,
            states=states,
            start_date=start_date,
            end_date=end_date,
            date_field=date_field,
            additional_filters=additional_filters
        )
        print(query)
        print(f"Generated WIQL Query:\n{query}\n")
        # Use organization-level WIQL query for maximum efficiency
        print("Using organization-level WIQL query for optimal performance...")
        all_work_items = []
        successful_projects = []
        try:
            # Execute organization-level WIQL query
            work_items_with_projects = self.execute_organization_wiql_query(
                query=query,
                target_projects=target_projects if not all_projects else None,
                project_names=project_names
            )
            # Filter out work items with 'Unknown' project id before proceeding
            if work_items_with_projects:
                filtered_work_items = [
                    item for item in work_items_with_projects
                    if item.get('project_id', None) not in (None, '', 'Unknown')
                ]
                if len(filtered_work_items) < len(work_items_with_projects):
                    skipped = len(work_items_with_projects) - len(filtered_work_items)
                    print(f"Skipped {skipped} work items with unknown project id to avoid invalid API calls.")
                work_items_with_projects = filtered_work_items
            if work_items_with_projects:
                filtered_work_items = [item for item in work_items_with_projects if item.get('project_id', None) not in (None, '', 'Unknown')]
                all_work_items = filtered_work_items
                successful_projects = list(set([item.get('project_id') for item in all_work_items]))
                print(f"Found {len(all_work_items)} work items across {len(successful_projects)} projects")
                if len(filtered_work_items) < len(work_items_with_projects):
                    print(f"Skipped {len(work_items_with_projects) - len(filtered_work_items)} work items with unknown project id")
            else:
                print("No work items found matching the criteria")
        except Exception as e:
            print(f"Organization-level query failed: {e}")
            print("Falling back to project-by-project approach...")
            for project in target_projects:
                proj_id = project['id']
                proj_name = project['name']
                if not proj_id or proj_id == "Unknown":
                    print(f"  Skipping project with unknown id (Name: {proj_name})")
                    continue
                try:
                    print(f"Querying project: {proj_name} ({proj_id})")
                    work_item_ids = self.execute_wiql_query(proj_id, query)
                    if work_item_ids:
                        work_items = self.get_work_item_details(proj_id, work_item_ids, proj_name)
                        for item in work_items:
                            item['project_id'] = proj_id
                            item['project_name'] = proj_name
                        all_work_items.extend(work_items)
                        successful_projects.append(proj_id)
                        print(f"  Found {len(work_items)} work items in {proj_name}")
                    else:
                        print(f"  No work items found in {proj_name}")
                except Exception as e:
                    print(f"  Error querying project {proj_name}: {e}")
                    continue
        if not all_work_items:
            print("No work items found across all projects.")
            return {
                "work_items": [],
                "kpis": self.calculate_comprehensive_kpi([]),
                "query_info": {
                    "total_items": 0,
                    "projects_queried": successful_projects,
                    "filters_applied": {
                        "assigned_to": assigned_to,
                        "work_item_types": work_item_types,
                        "states": states,
                        "date_range": f"{start_date or 'Any'} to {end_date or 'Any'}",
                        "date_field": date_field
                    }
                }
            }
        print("This is one work item----", all_work_items[0])
        # Calculate efficiency if requested
        if calculate_efficiency:
            print("Calculating efficiency metrics...")
            for item in all_work_items:
                try:
                    state_history = self.get_work_item_revisions(item['project_id'], item["id"], item['project_name'])
                    efficiency = self.calculate_active_time_efficiency(
                        state_history, productive_states, blocked_states
                    )
                    item["efficiency"] = efficiency
                except Exception as e:
                    print(f"Error calculating efficiency for work item {item['id']}: {e}")
                    item["efficiency"] = {}
        # Calculate comprehensive KPIs
        kpis = self.calculate_comprehensive_kpi(all_work_items)
        # Add start_date, target_date, close_date to each work item summary in the output
        for item in all_work_items:
            # These fields are already present, but ensure they are included in the summary
            item['start_date'] = item.get('start_date', '')
            item['target_date'] = item.get('target_date', '')
            item['closed_date'] = item.get('closed_date', '')
        return {
            "work_items": all_work_items,
            "kpis": kpis,
            "query_info": {
                "total_items": len(all_work_items),
                "projects_queried": successful_projects,
                "filters_applied": {
                    "assigned_to": assigned_to,
                    "work_item_types": work_item_types,
                    "states": states,
                    "date_range": f"{start_date or 'Any'} to {end_date or 'Any'}",
                    "date_field": date_field
                }
            }
        }
    
    def export_work_items_to_csv(self, 
                                work_items: List[Dict], 
                                filename: str = "work_items_export.csv") -> None:
        """
        Export work items data to CSV file.
        
        Args:
            work_items: List of work items to export
            filename: Output filename
        """
        if not work_items:
            print("No work items to export.")
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'ID', 'Title', 'Project Name', 'Assigned To', 'State', 'Work Item Type',
                    'Start Date', 'Closed Date', 'Target Date',
                    'Active Time (Hours)', 'Blocked Time (Hours)', 'Efficiency %'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for item in work_items:
                    efficiency = item.get("efficiency", {})
                    writer.writerow({
                        'ID': item['id'],
                        'Title': item['title'],
                        'Project Name': item.get('project_name', ''),
                        'Assigned To': item['assigned_to'],
                        'State': item['state'],
                        'Work Item Type': item['work_item_type'],
                        'Start Date': item.get('start_date', ''),
                        'Closed Date': item['closed_date'],
                        'Target Date': item['target_date'],
                        'Active Time (Hours)': efficiency.get('active_time_hours', 0),
                        'Blocked Time (Hours)': efficiency.get('blocked_time_hours', 0),
                        'Efficiency %': efficiency.get('efficiency_percentage', 0)
                    })
            
            print(f"Successfully exported {len(work_items)} work items to {filename}")
            
        except IOError as e:
            print(f"Error writing to CSV file {filename}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during CSV export: {e}")