import argparse
from commands import AzureDevOpsCommands
from AzureDevopsProjectOperations import AzureDevOpsProjectOperations
import os
from dotenv import load_dotenv

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

  --create-hook
      Creates a service hook for a specific project.
      Requires additional arguments:
        --project-id : The ID of the project to create the service hook for.
        --event-type : The event type that triggers the hook (e.g., 'build.complete').
        --hook-url   : The webhook URL to which the event data will be sent.
      Example:
        python main.py --create-hook --project-id <project_id> --event-type build.complete --hook-url <webhook_url>

  --project-specific-commands
      Perform operations on a specific project, such as listing work items or GitHub repositories.

Environment Variables:
  AZURE_DEVOPS_ORG   : Default Azure DevOps organization name.
  AZURE_DEVOPS_PAT   : Default Azure DevOps personal access token.

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


def main():
    parser = argparse.ArgumentParser(description="Azure DevOps CLI Utility Inbest")
    parser.add_argument("--organization", help="Azure DevOps organization name (optional, fallback to AZURE_DEVOPS_ORG environment variable)")
    parser.add_argument("--personal-access-token", help="Azure DevOps personal access token (optional, fallback to AZURE_DEVOPS_PAT environment variable)")
    
    # Global commands
    parser.add_argument("--list-projects", action="store_true", help="List all projects in the organization")
    parser.add_argument("--filter-tag", nargs="*", help="Filter projects by tags in the description (e.g., 'Software Factory')")
    parser.add_argument("--create-hook", action="store_true", help="Create a service hook for a project")
    parser.add_argument("--project-id", help="Project ID for the service hook or project-specific operations")
    parser.add_argument("--event-type", help="Event type for the service hook (e.g., 'build.complete')")
    parser.add_argument("--hook-url", help="Webhook URL for the service hook (optional, fallback to AZURE_DEVOPS_HOOK_URL environment variable)")
    parser.add_argument("--explain", action="store_true", help="Explain all commands and arguments")
    parser.add_argument("--create-hooks-for-filtered-projects", action="store_true",
                        help="Create service hooks for projects filtered by tags")
    parser.add_argument("--state-changed", action="store_true",
                        help="If set and event-type=workitem.updated, only trigger when State changes")
    parser.add_argument(
    "--filter-fields",
    action="store_true",
    help="If set, service hooks will track only specific fields (Priority, TargetDate, CommentCount)."
    )


    # Project-specific commands
    parser.add_argument("--list-work-items", action="store_true", help="List all work items in the project")
    parser.add_argument("--create-work-item", action="store_true", help="Create a new work item in the project")
    parser.add_argument("--work-item-type", help="Type of the work item to create (e.g., Bug, Task)")
    parser.add_argument("--work-item-title", help="Title of the new work item")
    parser.add_argument("--work-item-description", help="Description of the new work item")
    parser.add_argument("--list-github-repos", action="store_true", help="List GitHub repositories connected to the project")
    parser.add_argument("--list-subscriptions", action="store_true",
                        help="List service hook subscriptions for the specified project")
    parser.add_argument(
        "--create-filtered-hook",
        action="store_true",
        help="Create a service hook for workitem.updated with field filters (e.g., Priority, TargetDate, CommentCount)"
    )

    
    
    args = parser.parse_args()

    # Handle explain command
    if args.explain:
        explain_commands()
        return

    # Get organization and PAT from arguments or environment variables
    organization = args.organization or os.getenv("AZURE_DEVOPS_ORG")
    personal_access_token = args.personal_access_token or os.getenv("AZURE_DEVOPS_PAT")

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
            url=args.hook_url or os.getenv("AZURE_DEVOPS_HOOK_URL") or "https://default-webhook-url.com",
            state_changed=args.state_changed
        ),

        "create_hooks_for_filtered_projects": lambda: az_commands.create_hooks_for_filtered_projects(
            target_tags=args.filter_tag,
            event_type=args.event_type,
            url=args.hook_url or os.getenv("AZURE_DEVOPS_HOOK_URL") or "https://default-webhook-url.com",
            filter_fields=args.filter_fields  # Dynamically decides if field filtering should be applied
        ) if args.filter_tag and args.event_type else print(
            "Error: Missing arguments for creating service hooks. Provide --filter-tag and --event-type."
        ),

        "create_filtered_hook": lambda: az_commands.create_service_hook_with_field_filters(
            project_id=args.project_id,
            hook_url=args.hook_url or os.getenv("AZURE_DEVOPS_HOOK_URL") or "https://default-webhook-url.com"
        ) if args.create_filtered_hook else None,

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
        )
    }


    # Determine which global operation to execute
    for operation_name, operation_func in global_operations.items():
        if getattr(args, operation_name, False):
            operation_func()
            return

    # Handle project-specific operations
    if args.project_id:
        project_ops = AzureDevOpsProjectOperations(organization, personal_access_token, args.project_id)
        handle_project_operations(args, project_ops)
    else:
        print("Error: No valid operation provided.")
        parser.print_help()


if __name__ == "__main__":
    main()
