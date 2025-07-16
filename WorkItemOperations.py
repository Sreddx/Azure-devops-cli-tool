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
        
        # Smart date filtering for mixed states (closed + active items)
        if start_date or end_date:
            date_conditions = []
            
            # For closed items: use closed date
            closed_states = ['Closed', 'Done', 'Resolved']
            if any(state in closed_states for state in (states or [])):
                closed_condition_parts = []
                closed_states_str = "', '".join(closed_states)
                closed_condition_parts.append(f"[System.State] IN ('{closed_states_str}')")
                
                if start_date:
                    closed_condition_parts.append(f"[Microsoft.VSTS.Common.ClosedDate] >= '{start_date}'")
                if end_date:
                    closed_condition_parts.append(f"[Microsoft.VSTS.Common.ClosedDate] <= '{end_date}'")
                
                if len(closed_condition_parts) > 1:
                    date_conditions.append(f"({' AND '.join(closed_condition_parts)})")
            
            # For active/new items: use target date within timeframe
            active_states = ['Active', 'New', 'To Do', 'In Progress']
            if any(state in active_states for state in (states or [])):
                active_condition_parts = []
                active_states_str = "', '".join(active_states)
                active_condition_parts.append(f"[System.State] IN ('{active_states_str}')")
                
                if start_date:
                    active_condition_parts.append(f"[Microsoft.VSTS.Scheduling.TargetDate] >= '{start_date}'")
                if end_date:
                    active_condition_parts.append(f"[Microsoft.VSTS.Scheduling.TargetDate] <= '{end_date}'")
                
                if len(active_condition_parts) > 1:
                    date_conditions.append(f"({' AND '.join(active_condition_parts)})")
            
            # Combine date conditions with OR
            if date_conditions:
                # Remove the states filter from main conditions since it's handled in date conditions
                conditions = [c for c in conditions if not c.startswith('[System.State]')]
                conditions.append(f"({' OR '.join(date_conditions)})")
        else:
            # Fallback to original logic if no date filtering
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

    def calculate_fair_efficiency_metrics(self, 
                                         work_item: Dict,
                                         state_history: List[Dict], 
                                         productive_states: Optional[List[str]] = None,
                                         blocked_states: Optional[List[str]] = None) -> Dict:
        """
        Calculate fair efficiency metrics that encourage good development practices.
        
        Args:
            work_item: Work item details with dates and metadata
            state_history: List of state changes with timestamps
            productive_states: List of states considered productive (optional)
            blocked_states: List of states considered blocked (optional)
        Returns:
            Dictionary with enhanced efficiency metrics
        """
        if len(state_history) < 2:
            return {
                "active_time_hours": 0,
                "blocked_time_hours": 0,
                "total_time_hours": 0,
                "estimated_time_hours": 0,
                "efficiency_percentage": 0,
                "fair_efficiency_score": 0,
                "delivery_score": 0,
                "completion_bonus": 0,
                "delivery_timing_bonus": 0,
                "days_ahead_behind": 0,
                "state_breakdown": {},
                "was_reopened": False,
                "active_after_reopen": 0
            }
        
        # Calculate time in different states
        active_time = timedelta()
        blocked_time = timedelta()
        total_time = timedelta()
        state_breakdown = {}
        was_reopened = False
        active_after_reopen = timedelta()
        
        # Track if item was reopened (Closed -> Active pattern)
        for i in range(len(state_history) - 1):
            current_state = state_history[i]['state']
            next_state = state_history[i+1]['state']
            
            if current_state in ['Closed', 'Done', 'Resolved'] and next_state in (productive_states or ['Active']):
                was_reopened = True
            
            # Calculate time in each state
            next_change = datetime.fromisoformat(state_history[i+1]['changed_date'].replace('Z', '+00:00'))
            current_change = datetime.fromisoformat(state_history[i]['changed_date'].replace('Z', '+00:00'))
            
            # Calculate business hours only for productive states
            if productive_states is not None and current_state in productive_states:
                business_hours_in_state = self._calculate_business_hours(current_change, next_change)
                active_time += timedelta(hours=business_hours_in_state)
                
                # Track active time after reopening for bonus credit
                if was_reopened and i > 0:
                    prev_states = [h['state'] for h in state_history[:i]]
                    if any(state in ['Closed', 'Done', 'Resolved'] for state in prev_states):
                        active_after_reopen += timedelta(hours=business_hours_in_state)
            else:
                # For non-productive states, use regular time calculation
                time_in_state = next_change - current_change
                if blocked_states is not None and current_state in blocked_states:
                    blocked_time += time_in_state
            
            # Always calculate total time and state breakdown with regular time
            time_in_state = next_change - current_change
            total_time += time_in_state
            
            # Track time per state (use business hours for productive states)
            if current_state not in state_breakdown:
                state_breakdown[current_state] = timedelta()
            
            if productive_states is not None and current_state in productive_states:
                business_hours_in_state = self._calculate_business_hours(current_change, next_change)
                state_breakdown[current_state] += timedelta(hours=business_hours_in_state)
            else:
                state_breakdown[current_state] += time_in_state
        
        # Calculate estimated time from dates
        estimated_hours = self._calculate_estimated_time(work_item)
        
        # Calculate delivery timing
        delivery_metrics = self._calculate_delivery_timing(work_item)
        
        # Convert to hours
        active_hours = active_time.total_seconds() / 3600
        blocked_hours = blocked_time.total_seconds() / 3600
        total_hours = total_time.total_seconds() / 3600
        active_after_reopen_hours = active_after_reopen.total_seconds() / 3600
        
        # Calculate completion bonus (20% of estimated time)
        is_completed = work_item.get('state', '').lower() in ['closed', 'done', 'resolved']
        completion_bonus = (estimated_hours * 0.20) if is_completed else 0
        
        # Calculate fair efficiency score with bonuses
        # Base: active time + completion bonus + delivery timing bonus
        numerator = active_hours + completion_bonus + delivery_metrics['timing_bonus_hours']
        # Denominator: estimated time + late penalty mitigation (capped)
        denominator = estimated_hours + delivery_metrics['late_penalty_mitigation']
        
        if denominator > 0:
            fair_efficiency = (numerator / denominator) * 100
            # Cap at 150% to prevent unrealistic scores
            fair_efficiency = min(fair_efficiency, 150.0)
        else:
            fair_efficiency = 0
        
        # Traditional efficiency for comparison
        traditional_efficiency = (active_hours / total_hours) * 100 if total_hours > 0 else 0
        
        # Convert state breakdown to hours
        state_breakdown_hours = {
            state: td.total_seconds() / 3600 
            for state, td in state_breakdown.items()
        }
        
        return {
            "active_time_hours": round(active_hours, 2),
            "blocked_time_hours": round(blocked_hours, 2),
            "total_time_hours": round(total_hours, 2),
            "estimated_time_hours": round(estimated_hours, 2),
            "efficiency_percentage": round(traditional_efficiency, 2),  # Keep for comparison
            "fair_efficiency_score": round(fair_efficiency, 2),
            "delivery_score": round(delivery_metrics['delivery_score'], 2),
            "completion_bonus": round(completion_bonus, 2),
            "delivery_timing_bonus": round(delivery_metrics['timing_bonus_hours'], 2),
            "days_ahead_behind": delivery_metrics['days_difference'],
            "state_breakdown": state_breakdown_hours,
            "was_reopened": was_reopened,
            "active_after_reopen": round(active_after_reopen_hours, 2)
        }
    
    def _calculate_estimated_time(self, work_item: Dict) -> float:
        """
        Calculate estimated time for a work item based on start and target dates.
        
        Args:
            work_item: Work item with date fields
            
        Returns:
            Estimated time in hours
        """
        start_date = work_item.get('start_date')
        target_date = work_item.get('target_date')
        
        if start_date and target_date:
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                target = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
                duration = target - start
                
                # Convert to working hours (assume 8 hours per day, 5 days per week)
                days = duration.total_seconds() / 86400
                working_days = days * (5/7)  # Convert to working days
                hours = working_days * 8
                
                # Minimum 4 hours for any work item
                return max(hours, 4.0)
                
            except (ValueError, TypeError):
                pass
        
        # Fallback: use work item type to estimate
        work_item_type = work_item.get('work_item_type', '').lower()
        if 'user story' in work_item_type:
            return 16.0  # 2 days
        elif 'task' in work_item_type:
            return 8.0   # 1 day
        elif 'bug' in work_item_type:
            return 4.0   # 0.5 day
        else:
            return 8.0   # Default 1 day
    
    def _calculate_delivery_timing(self, work_item: Dict) -> Dict:
        """
        Calculate delivery timing metrics and bonuses/penalties.
        
        Args:
            work_item: Work item with date fields
            
        Returns:
            Dictionary with delivery timing metrics
        """
        target_date = work_item.get('target_date')
        closed_date = work_item.get('closed_date')
        
        if not target_date or not closed_date:
            return {
                'delivery_score': 100.0,
                'timing_bonus_hours': 0.0,
                'late_penalty_mitigation': 0.0,
                'days_difference': 0
            }
        
        try:
            target = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
            closed = datetime.fromisoformat(closed_date.replace('Z', '+00:00'))
            
            days_difference = (closed - target).total_seconds() / 86400
            
            if days_difference <= 0:
                # Early or on-time delivery
                if days_difference <= -7:
                    # Very early (7+ days early)
                    delivery_score = 130.0
                    timing_bonus_hours = abs(days_difference) * 1.0
                elif days_difference <= -3:
                    # Early (3-7 days early)
                    delivery_score = 120.0
                    timing_bonus_hours = abs(days_difference) * 0.5
                elif days_difference <= -1:
                    # Slightly early (1-3 days early)
                    delivery_score = 110.0
                    timing_bonus_hours = abs(days_difference) * 0.25
                else:
                    # On time
                    delivery_score = 100.0
                    timing_bonus_hours = 0.0
                    
                late_penalty_mitigation = 0.0
                
            else:
                # Late delivery with graduated penalties
                timing_bonus_hours = 0.0
                
                if days_difference <= 3:
                    delivery_score = 90.0
                    late_penalty_mitigation = 2.0  # Small mitigation
                elif days_difference <= 7:
                    delivery_score = 80.0
                    late_penalty_mitigation = 4.0
                elif days_difference <= 14:
                    delivery_score = 70.0
                    late_penalty_mitigation = 6.0
                else:
                    delivery_score = 60.0  # Floor at 60%
                    late_penalty_mitigation = 8.0  # Max mitigation
            
            return {
                'delivery_score': delivery_score,
                'timing_bonus_hours': timing_bonus_hours,
                'late_penalty_mitigation': late_penalty_mitigation,
                'days_difference': round(days_difference, 1)
            }
            
        except (ValueError, TypeError):
            return {
                'delivery_score': 100.0,
                'timing_bonus_hours': 0.0,
                'late_penalty_mitigation': 0.0,
                'days_difference': 0
            }
    
    def _calculate_business_hours(self, start_time: datetime, end_time: datetime, 
                                max_hours_per_day: float = 10.0) -> float:
        """
        Calculate business hours between two timestamps.
        Only counts Monday-Friday, max hours per day.
        
        Args:
            start_time: Start datetime (timezone-aware)
            end_time: End datetime (timezone-aware)
            max_hours_per_day: Maximum hours to count per working day
            
        Returns:
            Total business hours as float
        """
        if start_time >= end_time:
            return 0.0
        
        total_business_hours = 0.0
        current_date = start_time.date()
        end_date = end_time.date()
        
        # If same day, handle it specially
        if current_date == end_date:
            if current_date.weekday() < 5:  # Monday=0, Friday=4
                hours_on_day = (end_time - start_time).total_seconds() / 3600
                return min(hours_on_day, max_hours_per_day)
            else:
                return 0.0  # Weekend
        
        # Handle multi-day periods
        while current_date <= end_date:
            # Skip weekends (Monday=0, Sunday=6)
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
            
            if current_date == start_time.date():
                # First day: from start_time to end of day
                day_start = start_time
                day_end = datetime.combine(current_date, datetime.max.time()).replace(tzinfo=start_time.tzinfo)
                hours_on_day = (day_end - day_start).total_seconds() / 3600
                total_business_hours += min(hours_on_day, max_hours_per_day)
                
            elif current_date == end_time.date():
                # Last day: from start of day to end_time
                day_start = datetime.combine(current_date, datetime.min.time()).replace(tzinfo=end_time.tzinfo)
                day_end = end_time
                hours_on_day = (day_end - day_start).total_seconds() / 3600
                total_business_hours += min(hours_on_day, max_hours_per_day)
                
            else:
                # Full day in between
                total_business_hours += max_hours_per_day
            
            current_date += timedelta(days=1)
        
        return round(total_business_hours, 2)
    
    def calculate_comprehensive_kpi_per_developer(self, work_items: List[Dict]) -> Dict:
        """
        Calculate comprehensive KPIs separated by developer with fair efficiency metrics.
        
        Args:
            work_items: List of work items with enhanced efficiency data
        Returns:
            Dictionary with per-developer KPI metrics and overall summary
        """
        if not work_items:
            return {
                "overall_summary": {
                    "total_work_items": 0,
                    "total_developers": 0,
                    "average_fair_efficiency": 0,
                    "average_delivery_score": 0,
                    "total_active_hours": 0
                },
                "developer_metrics": {},
                "bottlenecks": []
            }
        
        # Group work items by developer
        developer_items = {}
        for item in work_items:
            assigned_to = item.get('assigned_to', 'Unassigned')
            if assigned_to not in developer_items:
                developer_items[assigned_to] = []
            developer_items[assigned_to].append(item)
        
        # Calculate metrics for each developer
        developer_metrics = {}
        all_state_occurrences = {}
        total_fair_efficiency = 0
        total_delivery_score = 0
        total_active_hours = 0
        total_developers = len(developer_items)
        
        for developer, items in developer_items.items():
            metrics = self._calculate_developer_metrics(items)
            developer_metrics[developer] = metrics
            
            # Aggregate for overall summary
            total_fair_efficiency += metrics['average_fair_efficiency']
            total_delivery_score += metrics['average_delivery_score']
            total_active_hours += metrics['total_active_hours']
            
            # Collect state data for bottleneck analysis
            for item in items:
                efficiency_data = item.get('efficiency', {})
                for state, hours in efficiency_data.get('state_breakdown', {}).items():
                    if state not in all_state_occurrences:
                        all_state_occurrences[state] = {'count': 0, 'total_hours': 0}
                    all_state_occurrences[state]['count'] += 1
                    all_state_occurrences[state]['total_hours'] += hours
        
        # Calculate overall bottlenecks
        bottlenecks = []
        for state, data in all_state_occurrences.items():
            avg_time = data['total_hours'] / data['count'] if data['count'] > 0 else 0
            bottlenecks.append({
                'state': state,
                'average_time_hours': round(avg_time, 2),
                'occurrences': data['count']
            })
        bottlenecks.sort(key=lambda x: x['average_time_hours'], reverse=True)
        
        # Overall summary
        overall_summary = {
            'total_work_items': len(work_items),
            'total_developers': total_developers,
            'average_fair_efficiency': round(total_fair_efficiency / total_developers, 2) if total_developers > 0 else 0,
            'average_delivery_score': round(total_delivery_score / total_developers, 2) if total_developers > 0 else 0,
            'total_active_hours': round(total_active_hours, 2)
        }
        
        return {
            'overall_summary': overall_summary,
            'developer_metrics': developer_metrics,
            'bottlenecks': bottlenecks[:5]
        }
    
    def _calculate_developer_metrics(self, work_items: List[Dict]) -> Dict:
        """
        Calculate detailed metrics for a single developer.
        
        Args:
            work_items: List of work items for one developer
            
        Returns:
            Dictionary with developer-specific metrics
        """
        if not work_items:
            return self._empty_developer_metrics()
        
        total_items = len(work_items)
        completed_items = 0
        items_with_efficiency = 0  # Only completed items have efficiency data
        on_time_count = 0
        total_fair_efficiency = 0
        total_delivery_score = 0
        total_active_hours = 0
        total_estimated_hours = 0
        total_days_ahead_behind = 0
        reopened_items = 0
        work_item_types = set()
        projects = set()
        
        delivery_timing_counts = {
            'early': 0, 'on_time': 0, 'late_1_3': 0, 
            'late_4_7': 0, 'late_8_14': 0, 'late_15_plus': 0
        }
        
        for item in work_items:
            # Basic counts
            work_item_types.add(item.get('work_item_type', 'Unknown'))
            projects.add(item.get('project_name', 'Unknown'))
            
            if item.get('state', '').lower() in ['closed', 'done', 'resolved']:
                completed_items += 1
            
            # Efficiency metrics (only for items with efficiency data - completed items)
            efficiency_data = item.get('efficiency', {})
            if efficiency_data and any(efficiency_data.values()):  # Has meaningful efficiency data
                items_with_efficiency += 1
                total_fair_efficiency += efficiency_data.get('fair_efficiency_score', 0)
                total_delivery_score += efficiency_data.get('delivery_score', 100)
                total_active_hours += efficiency_data.get('active_time_hours', 0)
                total_estimated_hours += efficiency_data.get('estimated_time_hours', 0)
                total_days_ahead_behind += efficiency_data.get('days_ahead_behind', 0)
                
                if efficiency_data.get('was_reopened', False):
                    reopened_items += 1
                
                # Delivery timing analysis (only for completed items)
                days_diff = efficiency_data.get('days_ahead_behind', 0)
                if days_diff <= 0:
                    if days_diff <= -1:
                        delivery_timing_counts['early'] += 1
                    else:
                        delivery_timing_counts['on_time'] += 1
                    on_time_count += 1
                elif days_diff <= 3:
                    delivery_timing_counts['late_1_3'] += 1
                elif days_diff <= 7:
                    delivery_timing_counts['late_4_7'] += 1
                elif days_diff <= 14:
                    delivery_timing_counts['late_8_14'] += 1
                else:
                    delivery_timing_counts['late_15_plus'] += 1
        
        # Calculate averages and percentages
        completion_rate = (completed_items / total_items) * 100
        
        # Efficiency metrics based only on completed items with efficiency data
        if items_with_efficiency > 0:
            on_time_delivery = (on_time_count / items_with_efficiency) * 100
            avg_fair_efficiency = total_fair_efficiency / items_with_efficiency
            avg_delivery_score = total_delivery_score / items_with_efficiency
            avg_days_ahead_behind = total_days_ahead_behind / items_with_efficiency
            reopened_rate = (reopened_items / items_with_efficiency) * 100
        else:
            on_time_delivery = 0
            avg_fair_efficiency = 0
            avg_delivery_score = 0
            avg_days_ahead_behind = 0
            reopened_rate = 0
        
        # Overall developer score (weighted combination)
        overall_score = (
            (avg_fair_efficiency * 0.4) +  # 40% fair efficiency
            (avg_delivery_score * 0.3) +    # 30% delivery score  
            (completion_rate * 0.2) +       # 20% completion rate
            (min(100, on_time_delivery) * 0.1)  # 10% on-time delivery (capped at 100)
        )
        
        return {
            'total_work_items': total_items,
            'completed_items': completed_items,
            'completion_rate': round(completion_rate, 2),
            'on_time_delivery_percentage': round(on_time_delivery, 2),
            'average_fair_efficiency': round(avg_fair_efficiency, 2),
            'average_delivery_score': round(avg_delivery_score, 2),
            'overall_developer_score': round(overall_score, 2),
            'total_active_hours': round(total_active_hours, 2),
            'total_estimated_hours': round(total_estimated_hours, 2),
            'average_days_ahead_behind': round(avg_days_ahead_behind, 2),
            'reopened_items_handled': reopened_items,
            'reopened_rate': round(reopened_rate, 2),
            'work_item_types_count': len(work_item_types),
            'work_item_types': list(work_item_types),
            'projects_count': len(projects),
            'projects': list(projects),
            'delivery_timing_breakdown': delivery_timing_counts
        }
    
    def _empty_developer_metrics(self) -> Dict:
        """Return empty metrics structure for developers with no work items."""
        return {
            'total_work_items': 0,
            'completed_items': 0,
            'completion_rate': 0,
            'on_time_delivery_percentage': 0,
            'average_fair_efficiency': 0,
            'average_delivery_score': 0,
            'overall_developer_score': 0,
            'total_active_hours': 0,
            'total_estimated_hours': 0,
            'average_days_ahead_behind': 0,
            'reopened_items_handled': 0,
            'reopened_rate': 0,
            'work_item_types_count': 0,
            'work_item_types': [],
            'projects_count': 0,
            'projects': [],
            'delivery_timing_breakdown': {
                'early': 0, 'on_time': 0, 'late_1_3': 0,
                'late_4_7': 0, 'late_8_14': 0, 'late_15_plus': 0
            }
        }
    
    def execute_organization_wiql_query(self, 
                                       query: str, 
                                       target_projects: Optional[List[Dict]] = None,
                                       project_names: Optional[List[str]] = None) -> List[Dict]:
        print("Executing organization-level WIQL query...")
        endpoint = f"_apis/wit/wiql?api-version={self.get_api_version('wiql')}"
        if target_projects and len(target_projects) < 20:
            project_names = [p['name'] for p in target_projects]
            project_filter = "', '".join(project_names)
            if "WHERE" in query.upper():
                query = query.replace("WHERE", f"WHERE [System.TeamProject] IN ('{project_filter}') AND")
            else:
                query = query.replace("FROM WorkItems", f"FROM WorkItems WHERE [System.TeamProject] IN ('{project_filter}')")
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
            # Include both completed and active/new items for comprehensive analysis
            states = ["Closed", "Done", "Resolved", "Active", "New", "To Do", "In Progress"]
            
        # Default to last 30 days if no date range provided
        if start_date is None and end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            print(f"No date range provided, defaulting to last 30 days: {start_date} to {end_date}")
            
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
                "kpis": self.calculate_comprehensive_kpi_per_developer([]),
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
        print(f"DEBUG - Date filtering parameters:")
        print(f"  start_date: {start_date}")
        print(f"  end_date: {end_date}")
        print(f"  date_field: {date_field}")
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
                "kpis": self.calculate_comprehensive_kpi_per_developer([]),
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
        # Display work items with their revision history for verification
        print(f"\n{'='*60}")
        print("WORK ITEMS WITH REVISION HISTORY")
        print(f"{'='*60}")
        for i, item in enumerate(all_work_items[:10]):  # Show first 3 work items
            print(f"\nWork Item #{i+1}:")
            print(f"  ID: {item['id']}")
            print(f"  Title: {item['title'][:80]}...")
            print(f"  Project: {item.get('project_name', 'Unknown')} ({item.get('project_id', 'Unknown')})")
            print(f"  Assigned To: {item['assigned_to']}")
            print(f"  Current State: {item['state']}")
            print(f"  Work Item Type: {item['work_item_type']}")
            print(f"  Start Date: {item.get('start_date', 'Not set')}")
            print(f"  Target Date: {item.get('target_date', 'Not set')}")
            print(f"  Closed Date: {item.get('closed_date', 'Not closed')}")
            
            # Get and display revision history
            try:
                state_history = self.get_work_item_revisions(item['project_id'], item["id"], item['project_name'])
                print(f"  Revision History ({len(state_history)} revisions):")
                for j, revision in enumerate(state_history):
                    print(f"    Rev {revision['revision']}: {revision['state']} | {revision['changed_date']} | By: {revision['changed_by']}")
                    if revision.get('reason'):
                        print(f"      Reason: {revision['reason']}")
                
                # Show what productive/blocked states would be interpreted as
                print(f"  Productive States Provided: {productive_states}")
                print(f"  Blocked States Provided: {blocked_states}")
                
                if productive_states:
                    productive_revisions = [r for r in state_history if r['state'] in productive_states]
                    print(f"  Revisions in Productive States: {len(productive_revisions)}")
                    for r in productive_revisions:
                        print(f"    - {r['state']} (Rev {r['revision']})")
                
                if blocked_states:
                    blocked_revisions = [r for r in state_history if r['state'] in blocked_states]
                    print(f"  Revisions in Blocked States: {len(blocked_revisions)}")
                    for r in blocked_revisions:
                        print(f"    - {r['state']} (Rev {r['revision']})")
                        
            except Exception as e:
                print(f"  ERROR getting revision history: {e}")
            
            print(f"  {'-'*50}")
        
        if len(all_work_items) > 3:
            print(f"\n... and {len(all_work_items) - 3} more work items\n")
            
        print(f"{'='*60}")
        
        # Calculate efficiency if requested
        if calculate_efficiency:
            print("Calculating enhanced efficiency metrics...")
            for item in all_work_items:
                try:
                    state_history = self.get_work_item_revisions(item['project_id'], item["id"], item['project_name'])
                    efficiency = self.calculate_fair_efficiency_metrics(
                        item, state_history, productive_states, blocked_states
                    )
                    item["efficiency"] = efficiency
                except Exception as e:
                    print(f"Error calculating efficiency for work item {item['id']}: {e}")
                    item["efficiency"] = {}
        # Calculate comprehensive KPIs per developer
        kpis = self.calculate_comprehensive_kpi_per_developer(all_work_items)
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
    
    def export_enhanced_work_items_to_csv(self, 
                                        work_items: List[Dict],
                                        kpis: Dict,
                                        base_filename: str = "work_items_export") -> None:
        """
        Export enhanced work items data and per-developer metrics to CSV files.
        
        Args:
            work_items: List of work items with enhanced efficiency data
            kpis: KPI data with per-developer metrics
            base_filename: Base filename for exports (without extension)
        """
        if not work_items:
            print("No work items to export.")
            return
        
        try:
            # Export detailed work items
            items_filename = f"{base_filename}_detailed.csv"
            with open(items_filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'ID', 'Title', 'Project Name', 'Assigned To', 'State', 'Work Item Type',
                    'Start Date', 'Target Date', 'Closed Date', 'Estimated Hours',
                    'Active Time (Hours)', 'Blocked Time (Hours)', 'Traditional Efficiency %',
                    'Fair Efficiency Score', 'Delivery Score', 'Days Ahead/Behind Target',
                    'Completion Bonus', 'Timing Bonus', 'Was Reopened', 'Active After Reopen'
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
                        'Target Date': item.get('target_date', ''),
                        'Closed Date': item.get('closed_date', ''),
                        'Estimated Hours': efficiency.get('estimated_time_hours', 0),
                        'Active Time (Hours)': efficiency.get('active_time_hours', 0),
                        'Blocked Time (Hours)': efficiency.get('blocked_time_hours', 0),
                        'Traditional Efficiency %': efficiency.get('efficiency_percentage', 0),
                        'Fair Efficiency Score': efficiency.get('fair_efficiency_score', 0),
                        'Delivery Score': efficiency.get('delivery_score', 0),
                        'Days Ahead/Behind Target': efficiency.get('days_ahead_behind', 0),
                        'Completion Bonus': efficiency.get('completion_bonus', 0),
                        'Timing Bonus': efficiency.get('delivery_timing_bonus', 0),
                        'Was Reopened': efficiency.get('was_reopened', False),
                        'Active After Reopen': efficiency.get('active_after_reopen', 0)
                    })
            
            print(f"Successfully exported {len(work_items)} detailed work items to {items_filename}")
            
            # Export developer summary
            summary_filename = f"{base_filename}_developer_summary.csv"
            developer_metrics = kpis.get('developer_metrics', {})
            
            if developer_metrics:
                with open(summary_filename, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = [
                        'Developer', 'Total Work Items', 'Completed Items', 'Completion Rate %',
                        'On-Time Delivery %', 'Average Fair Efficiency', 'Average Delivery Score',
                        'Overall Developer Score', 'Total Active Hours', 'Total Estimated Hours',
                        'Avg Days Ahead/Behind', 'Reopened Items Handled', 'Reopened Rate %',
                        'Work Item Types', 'Projects Count', 'Early Deliveries', 'On-Time Deliveries',
                        'Late 1-3 Days', 'Late 4-7 Days', 'Late 8-14 Days', 'Late 15+ Days'
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for developer, metrics in developer_metrics.items():
                        timing = metrics.get('delivery_timing_breakdown', {})
                        writer.writerow({
                            'Developer': developer,
                            'Total Work Items': metrics.get('total_work_items', 0),
                            'Completed Items': metrics.get('completed_items', 0),
                            'Completion Rate %': metrics.get('completion_rate', 0),
                            'On-Time Delivery %': metrics.get('on_time_delivery_percentage', 0),
                            'Average Fair Efficiency': metrics.get('average_fair_efficiency', 0),
                            'Average Delivery Score': metrics.get('average_delivery_score', 0),
                            'Overall Developer Score': metrics.get('overall_developer_score', 0),
                            'Total Active Hours': metrics.get('total_active_hours', 0),
                            'Total Estimated Hours': metrics.get('total_estimated_hours', 0),
                            'Avg Days Ahead/Behind': metrics.get('average_days_ahead_behind', 0),
                            'Reopened Items Handled': metrics.get('reopened_items_handled', 0),
                            'Reopened Rate %': metrics.get('reopened_rate', 0),
                            'Work Item Types': len(metrics.get('work_item_types', [])),
                            'Projects Count': metrics.get('projects_count', 0),
                            'Early Deliveries': timing.get('early', 0),
                            'On-Time Deliveries': timing.get('on_time', 0),
                            'Late 1-3 Days': timing.get('late_1_3', 0),
                            'Late 4-7 Days': timing.get('late_4_7', 0),
                            'Late 8-14 Days': timing.get('late_8_14', 0),
                            'Late 15+ Days': timing.get('late_15_plus', 0)
                        })
                
                print(f"Successfully exported developer summary to {summary_filename}")
            
        except IOError as e:
            print(f"Error writing to CSV files: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during CSV export: {e}")