import argparse
from commands import AzureDevOpsCommands
from AzureDevopsProjectOperations import AzureDevOpsProjectOperations
from WorkItemOperations import WorkItemOperations
from config import Config
import os
from dotenv import load_dotenv
import json

load_dotenv(".env")

def explain_commands():
    """
    Explains all available commands and their arguments.
    """
    explanation = """
Azure DevOps CLI Utility Inbest:

Commands:
  --list-projects
      Lists all projects in the specified Azure DevOps organization.
      Example:
        python main.py --list-projects

  --filter-tag
      Filter projects by tags in their descriptions.
      Example:
        python main.py --list-projects --filter-tag "Software Factory" "Production"

  --create-hook
      Creates a service hook for a specific project.
      Required arguments:
        --project-id : The ID of the project to create the service hook for.
        --event-type : The event type that triggers the hook (e.g., 'workitem.updated').
      Optional arguments:
        --hook-url   : The webhook URL (defaults to configured URL for event type).
        --state-changed : Only trigger on state changes for workitem.updated.
      Example:
        python main.py --create-hook --project-id <project_id> --event-type workitem.updated

  --remove-hook
      Removes service hook subscriptions.
      Required arguments:
        --project-id : The ID of the project containing the hook.
      Optional arguments:
        --subscription-id : The ID of the specific subscription to remove (removes all if not specified).
      Example:
        python main.py --remove-hook --project-id <project_id> --subscription-id <subscription_id>

  --list-subscriptions
      Lists service hook subscriptions for a project.
      Required arguments:
        --project-id : The ID of the project to list subscriptions for.
      Example:
        python main.py --list-subscriptions --project-id <project_id>

  --create-hooks-for-filtered-projects
      Creates service hooks for projects matching specified tags.
      Required arguments:
        --filter-tag : List of tags to filter projects by.
        --event-type : The event type for the service hook.
      Optional arguments:
        --hook-url : The webhook URL (defaults to configured URL for event type).
        --state-changed : Only trigger on state changes for workitem.updated.
      Example:
        python main.py --create-hooks-for-filtered-projects --filter-tag "Production" --event-type workitem.updated

  --list-and-upgrade-webhooks
      Lists projects by tag and upgrades their webhooks.
      Required arguments:
        --filter-tag : List of tags to filter projects by.
      Example:
        python main.py --list-and-upgrade-webhooks --filter-tag "Production"

  --query-work-items
      Query work items with dynamic filtering and KPI calculations.
      Project scope (choose one):
        --project-id : Query a specific project ID.
        --project-names : Query specific projects by name (comma-separated).
        (No project args) : Query ALL projects in the organization.
      Optional arguments:
        --assigned-to : List of users to filter by (comma-separated).
        --work-item-types : List of work item types (comma-separated).
        --states : List of states to filter by (comma-separated).
        --start-date : Start date for filtering (YYYY-MM-DD format).
        --end-date : End date for filtering (YYYY-MM-DD format).
        --date-field : Field to use for date filtering (default: ClosedDate).
        --no-efficiency : Skip efficiency calculations for faster results.
        --export-csv : Export results to CSV file.
        --area-path : Filter by area path.
        --iteration-path : Filter by iteration path.
        --all-projects : Query all projects (skip smart filtering based on user activity).
        --max-projects : Maximum number of projects to check for user activity (default: 50).
      Examples:
        # Query projects with user activity (smart filtering)
        python main.py --query-work-items --assigned-to "Carlos Vazquez,Alex Valenzuela"
        
        # Query all projects (no smart filtering)
        python main.py --query-work-items --assigned-to "Carlos Vazquez,Alex Valenzuela" --all-projects
        
        # Query more projects for user activity (check up to 100 projects)
        python main.py --query-work-items --assigned-to "Carlos Vazquez,Alex Valenzuela" --max-projects 100
        
        # Query specific projects
        python main.py --query-work-items --project-names "ProjectA,ProjectB" --states "Closed,Done"
        
        # Query single project
        python main.py --query-work-items --project-id <project_id> --start-date "2025-06-01"

Environment Variables:
  AZURE_DEVOPS_ORG   : Default Azure DevOps organization name.
  AZURE_DEVOPS_PAT   : Default Azure DevOps personal access token.
  AZURE_DEVOPS_WORKITEM_WEBHOOK_URL : Default webhook URL for workitem.updated events.
  AZURE_DEVOPS_BUILD_WEBHOOK_URL : Default webhook URL for build.complete events.
  AZURE_DEVOPS_RELEASE_WEBHOOK_URL : Default webhook URL for release.deployment.completed events.

Use --help for a detailed usage guide.
"""
    print(explanation)


def handle_project_operations(args, project_ops):
    """
    Dispatch table for project-specific operations.
    """
    operations = {
        "list_work_items": project_ops.list_work_items,
        "create_work_item": lambda: project_ops.create_work_item(
            work_item_type=args.work_item_type,
            title=args.work_item_title,
            description=args.work_item_description
        ),
        "list_github_repos": project_ops.list_github_repositories
    }

    # Determine which operation to execute
    for operation_name, operation_func in operations.items():
        if getattr(args, operation_name, False):
            operation_func()
            return

    print("Error: No valid project-specific operation provided.")


def handle_work_item_query(args, organization, personal_access_token):
    """
    Handle work item querying with dynamic filtering and KPI calculations.
    """
    # Parse comma-separated values
    assigned_to = args.assigned_to.split(',') if args.assigned_to else None
    work_item_types = args.work_item_types.split(',') if args.work_item_types else None
    states = args.states.split(',') if args.states else None
    project_names = args.project_names.split(',') if args.project_names else None
    
    # Build additional filters
    additional_filters = {}
    if args.area_path:
        additional_filters['area_path'] = args.area_path
    if args.iteration_path:
        additional_filters['iteration_path'] = args.iteration_path
    
    # Create WorkItemOperations instance
    work_item_ops = WorkItemOperations(organization, personal_access_token)
    
    # Determine query scope
    if args.project_id:
        print(f"Querying single project: {args.project_id}")
        query_scope = "single project"
    else:
        if project_names:
            print(f"Querying filtered projects: {', '.join(project_names)}")
            query_scope = f"projects: {', '.join(project_names)}"
        elif args.all_projects:
            print("Querying ALL projects in organization (forced)")
            query_scope = "all projects (forced)"
        elif assigned_to:
            print(f"Querying projects with activity for: {', '.join(assigned_to)}")
            query_scope = f"projects with activity for: {', '.join(assigned_to)}"
        else:
            print("Querying ALL projects in organization")
            query_scope = "all projects"
    
    # Execute query
    result = work_item_ops.get_work_items_with_efficiency(
        project_id=args.project_id,
        project_names=project_names,
        assigned_to=assigned_to,
        work_item_types=work_item_types,
        states=states,
        start_date=args.start_date,
        end_date=args.end_date,
        date_field=args.date_field,
        additional_filters=additional_filters if additional_filters else None,
        calculate_efficiency=not args.no_efficiency,
        all_projects=args.all_projects,
        max_projects=args.max_projects
    )
    
    # Display results
    print("\n" + "="*80)
    print("WORK ITEMS QUERY RESULTS")
    print("="*80)
    
    # Query info
    query_info = result.get('query_info', {})
    print(f"Query scope: {query_scope}")
    print(f"Total items found: {query_info.get('total_items', 0)}")
    
    # Show projects queried
    projects_queried = query_info.get('projects_queried', [])
    if projects_queried:
        print(f"Projects queried: {', '.join(projects_queried)}")
    
    filters = query_info.get('filters_applied', {})
    if filters.get('assigned_to'):
        print(f"Assigned to: {', '.join(filters['assigned_to'])}")
    if filters.get('work_item_types'):
        print(f"Work item types: {', '.join(filters['work_item_types'])}")
    if filters.get('states'):
        print(f"States: {', '.join(filters['states'])}")
    print(f"Date range: {filters.get('date_range', 'Any')}")
    
    # KPIs
    kpis = result.get('kpis', {})
    if kpis:
        print(f"\nKPI SUMMARY:")
        print(f"  On-time delivery: {kpis.get('on_time_delivery_percentage', 0)}%")
        print(f"  Average efficiency: {kpis.get('average_efficiency_percentage', 0)}%")
        print(f"  Total active hours: {kpis.get('total_active_hours', 0)}")
        print(f"  Total blocked hours: {kpis.get('total_blocked_hours', 0)}")
        
        bottlenecks = kpis.get('bottlenecks', [])
        if bottlenecks:
            print(f"\nTOP BOTTLENECKS:")
            for i, bottleneck in enumerate(bottlenecks[:3], 1):
                print(f"  {i}. {bottleneck['state']}: {bottleneck['average_time_hours']}h avg ({bottleneck['occurrences']} occurrences)")
    
    # Work items summary
    work_items = result.get('work_items', [])
    if work_items:
        print(f"\nWORK ITEMS SUMMARY:")
        for item in work_items[:5]:  # Show first 5
            efficiency = item.get('efficiency', {})
            project_info = f" | Project: {item.get('project_name', 'Unknown')}" if item.get('project_name') else ""
            print(f"  ID {item['id']}: {item['title'][:50]}...")
            print(f"    Assigned: {item['assigned_to']} | State: {item['state']}{project_info}")
            if efficiency:
                print(f"    Efficiency: {efficiency.get('efficiency_percentage', 0)}% | Active: {efficiency.get('active_time_hours', 0)}h")
            print()
        
        if len(work_items) > 5:
            print(f"... and {len(work_items) - 5} more items")
    
    # Export to CSV if requested
    if args.export_csv:
        work_item_ops.export_work_items_to_csv(work_items, args.export_csv)
    
    print("\n" + "="*80)


def main():
    parser = argparse.ArgumentParser(description="Azure DevOps CLI Utility Inbest")
    parser.add_argument("--organization", help="Azure DevOps organization name (optional, fallback to AZURE_DEVOPS_ORG environment variable)")
    parser.add_argument("--personal-access-token", help="Azure DevOps personal access token (optional, fallback to AZURE_DEVOPS_PAT environment variable)")
    
    # Global commands
    parser.add_argument("--list-projects", action="store_true", help="List all projects in the organization")
    parser.add_argument("--filter-tag", nargs="*", help="Filter projects by tags in the description (e.g., 'Software Factory')")
    parser.add_argument("--create-hook", action="store_true", help="Create a service hook for a project")
    parser.add_argument("--remove-hook", action="store_true", help="Remove service hook subscriptions")
    parser.add_argument("--project-id", help="Project ID for the service hook or project-specific operations")
    parser.add_argument("--subscription-id", help="Subscription ID for removing specific service hooks")
    parser.add_argument("--event-type", help="Event type for the service hook (e.g., 'workitem.updated')")
    parser.add_argument("--hook-url", help="Webhook URL for the service hook (optional, fallback to configured URL)")
    parser.add_argument("--explain", action="store_true", help="Explain all commands and arguments")
    parser.add_argument("--create-hooks-for-filtered-projects", action="store_true",
                        help="Create service hooks for projects filtered by tags")
    parser.add_argument("--state-changed", action="store_true",
                        help="If set and event-type=workitem.updated, only trigger when State changes")
    parser.add_argument("--list-and-upgrade-webhooks", action="store_true", help="List projects by tag and upgrade their webhooks")
    parser.add_argument("--list-subscriptions", action="store_true",
                        help="List service hook subscriptions for the specified project")

    # Project-specific commands
    parser.add_argument("--list-work-items", action="store_true", help="List all work items in the project")
    parser.add_argument("--create-work-item", action="store_true", help="Create a new work item in the project")
    parser.add_argument("--work-item-type", help="Type of the work item to create (e.g., Bug, Task)")
    parser.add_argument("--work-item-title", help="Title of the new work item")
    parser.add_argument("--work-item-description", help="Description of the new work item")
    parser.add_argument("--list-github-repos", action="store_true", help="List GitHub repositories connected to the project")
    parser.add_argument(
        "--create-filtered-hook",
        action="store_true",
        help="Create a service hook for workitem.updated with field filters (e.g., Priority, TargetDate, CommentCount)"
    )

    # Command to create standard hooks
    parser.add_argument("--create-standard-hooks", action="store_true",
                        help="Create a standard set of three webhooks (created, updated-assigned, updated-state) for a specific project (--project-id) or filtered projects (--filter-tag)")

    # Command to export projects to CSV
    parser.add_argument("--export-projects-csv", action="store_true",
                        help="Export all projects (Name, ID, Tags) to projects_export.csv")

    # Work item querying arguments
    parser.add_argument("--query-work-items", action="store_true",
                        help="Query work items with dynamic filtering and KPI calculations")
    parser.add_argument("--assigned-to", help="Comma-separated list of users to filter by")
    parser.add_argument("--work-item-types", help="Comma-separated list of work item types")
    parser.add_argument("--states", help="Comma-separated list of states to filter by")
    parser.add_argument("--start-date", help="Start date for filtering (YYYY-MM-DD format)")
    parser.add_argument("--end-date", help="End date for filtering (YYYY-MM-DD format)")
    parser.add_argument("--date-field", default="ClosedDate", help="Field to use for date filtering")
    parser.add_argument("--no-efficiency", action="store_true", help="Skip efficiency calculations")
    parser.add_argument("--export-csv", help="Export results to CSV file")
    parser.add_argument("--area-path", help="Filter by area path")
    parser.add_argument("--iteration-path", help="Filter by iteration path")
    parser.add_argument("--project-names", help="Comma-separated list of project names to filter by (for cross-project queries)")
    parser.add_argument("--all-projects", action="store_true", help="Query all projects (skip smart filtering based on user activity)")
    parser.add_argument("--max-projects", type=int, default=50, help="Maximum number of projects to check for user activity (default: 50)")
    
    args = parser.parse_args()

    # Handle explain command
    if args.explain:
        explain_commands()
        return

    # Get organization and PAT from arguments or environment variables
    organization = args.organization or Config.AZURE_DEVOPS_ORG
    personal_access_token = args.personal_access_token or Config.AZURE_DEVOPS_PAT

    print("Using organization:", organization)
    
    
    if not organization:
        print("Error: Azure DevOps organization is required. Provide it via --organization or set AZURE_DEVOPS_ORG.")
        return
    if not personal_access_token:
        print("Error: Azure DevOps personal access token is required. Provide it via --personal-access-token or set AZURE_DEVOPS_PAT.")
        return

    az_commands = AzureDevOpsCommands(organization, personal_access_token)

    # Dispatch table for global operations
    global_operations = {
        "list_projects": lambda: az_commands.list_projects_with_tag_filter(args.filter_tag) 
            if args.filter_tag else az_commands.list_projects(),

        "list_subscriptions": lambda: az_commands.list_subscriptions(args.project_id),

        "create_hook": lambda: az_commands.create_service_hook(
            project_id=args.project_id,
            event_type=args.event_type,
            hook_url=args.hook_url,
            state_changed=args.state_changed
        ) if args.project_id and args.event_type else print(
            "Error: --project-id and --event-type are required to create a service hook."
        ),

        "remove_hook": lambda: az_commands.remove_service_hook(
            project_id=args.project_id,
            subscription_id=args.subscription_id
        ) if args.project_id else print(
            "Error: --project-id is required to remove a service hook."
        ),

        "create_hooks_for_filtered_projects": lambda: az_commands.create_hooks_for_filtered_projects(
            target_tags=args.filter_tag,
            event_type=args.event_type,
            hook_url=args.hook_url,
            state_changed=args.state_changed
        ) if args.filter_tag and args.event_type else print(
            "Error: Missing arguments for creating service hooks. Provide --filter-tag and --event-type."
        ),

        "list_work_items": lambda: AzureDevOpsProjectOperations(
            organization, personal_access_token, args.project_id
        ).list_work_items() if args.project_id else print(
            "Error: --project-id is required to list work items."
        ),

        "create_work_item": lambda: AzureDevOpsProjectOperations(
            organization, personal_access_token, args.project_id
        ).create_work_item(
            work_item_type=args.work_item_type,
            title=args.work_item_title,
            description=args.work_item_description
        ) if args.project_id and args.work_item_type and args.work_item_title else print(
            "Error: Missing required arguments for creating work item."
        ),

        "list_github_repos": lambda: AzureDevOpsProjectOperations(
            organization, personal_access_token, args.project_id
        ).list_github_repositories() if args.project_id else print(
            "Error: --project-id is required to list GitHub repositories."
        ),

        "list_and_upgrade_webhooks": lambda: az_commands.list_and_update_webhooks(args.filter_tag) if args.filter_tag else print(
            "Error: --filter-tag is required to list and upgrade webhooks."
        ),

        "create_standard_hooks": lambda: (
            print(f"Debug - main.py: Calling create_standard_hooks with project_id={args.project_id}, target_tags={args.filter_tag}"),
            az_commands.create_standard_hooks(
                project_id=args.project_id,
                target_tags=args.filter_tag
            )
        )[1],

        "export_projects_csv": lambda: az_commands.export_projects_to_csv(),
        
        "query_work_items": lambda: handle_work_item_query(args, organization, personal_access_token),
    }


    # Determine which global operation to execute
    for operation_name, operation_func in global_operations.items():
        if getattr(args, operation_name, False):
            operation_func()
            return

    # Handle project-specific operations (if no global operation matched and project_id is given)
    if args.project_id and not any(getattr(args, op, False) for op in global_operations):
        project_ops = AzureDevOpsProjectOperations(organization, personal_access_token, args.project_id)
        handle_project_operations(args, project_ops)
    elif not any(getattr(args, op, False) for op in global_operations):
        print("Error: No valid operation provided or required arguments missing.")
        parser.print_help()


if __name__ == "__main__":
    main()
