# Azure DevOps CLI Utility

A command-line interface (CLI) tool to interact with Azure DevOps for managing projects, service hooks, work items, and more.

## Prerequisites

- Python 3.x
- Pip (Python package installer)

## Dependencies

Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

The dependencies are:
- `python-dotenv`: For loading environment variables from a `.env` file.
- `requests`: For making HTTP requests to the Azure DevOps API.
- `azure-devops`: Official Microsoft Azure DevOps Python client (though this tool uses direct REST API calls primarily).
- `argparse`: For parsing command-line arguments.

## Configuration

This tool uses environment variables for configuration, primarily for Azure DevOps credentials. Create a `.env` file in the root directory of the project:

```plaintext
# .env
AZURE_DEVOPS_ORG=<Your Azure DevOps Organization Name>
AZURE_DEVOPS_PAT=<Your Personal Access Token>
AZURE_DEVOPS_WORKITEM_WEBHOOK_URL=<Optional: Default webhook URL for workitem.updated>
AZURE_DEVOPS_BUILD_WEBHOOK_URL=<Optional: Default webhook URL for build.complete>
AZURE_DEVOPS_RELEASE_WEBHOOK_URL=<Optional: Default webhook URL for release.deployment.completed>
STANDARD_HOOK_PROJECT_IDS=<Optional: Comma-separated list of project IDs for --create-standard-hooks>
```

- **`AZURE_DEVOPS_ORG`**: Your Azure DevOps organization name (e.g., `YourOrgName` in `dev.azure.com/YourOrgName`).
- **`AZURE_DEVOPS_PAT`**: A Personal Access Token (PAT) with appropriate permissions (e.g., `Project and Team: Read`, `Service Hooks: Read & write`, `Work Items: Read & write`). Generate one from your Azure DevOps user settings.
- **Webhook URLs**: Optional default URLs for specific event types if you don't provide `--hook-url` when creating hooks.

You can also provide the organization and PAT via command-line arguments (`--organization` and `--personal-access-token`), which will override the environment variables.

## Usage

Run the tool using `python main.py` followed by the desired command and options.

```bash
python main.py <command> [options]
```

To see a detailed explanation of all commands and their arguments, run:

```bash
python main.py --explain
```

## Available Commands

Here are the main commands available:

### Project Management

- **List Projects:**
  ```bash
  python main.py --list-projects
  ```
- **List Projects by Tag:** Filter projects based on tags found in their description (requires tags to be in a specific JSON format within the description).
  ```bash
  python main.py --list-projects --filter-tag "Software Factory" "Production"
  ```
- **Export Projects to CSV:** Fetches all projects and exports their Name, ID, and parsed Tags (from description) to a file named `projects_export.csv`.
  ```bash
  python main.py --export-projects-csv
  ```

### Service Hook Management

- **List Subscriptions (Hooks) for a Project:**
  ```bash
  python main.py --list-subscriptions --project-id <project_id>
  ```
- **Create a Service Hook:**
  ```bash
  # Basic hook creation (uses default URL from config/.env if available)
  python main.py --create-hook --project-id <project_id> --event-type workitem.updated

  # Specify webhook URL
  python main.py --create-hook --project-id <project_id> --event-type build.complete --hook-url https://my-build-webhook.com

  # Create workitem.updated hook triggering only on State changes
  python main.py --create-hook --project-id <project_id> --event-type workitem.updated --state-changed
  ```
- **Remove a Specific Service Hook:**
  ```bash
  python main.py --remove-hook --project-id <project_id> --subscription-id <subscription_id>
  ```
- **Remove All Service Hooks for a Project:**
  ```bash
  python main.py --remove-hook --project-id <project_id>
  ```
- **Create Hooks for Filtered Projects:** Creates hooks for all projects matching specific tags.
  ```bash
  python main.py --create-hooks-for-filtered-projects --filter-tag "Production" --event-type workitem.updated --hook-url https://prod-hooks.com
  ```
  **Specific Examples:**
  ```bash
  # Create 'workitem.created' hook for "Software Factory" projects
  python main.py --create-hooks-for-filtered-projects --filter-tag "Software Factory" --event-type workitem.created --hook-url "https://prod-17.northcentralus.logic.azure.com:443/workflows/508aabfd2a114a949be865d9ace951b5/triggers/Se_crea_un_nuevo_work_item/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2FSe_crea_un_nuevo_work_item%2Frun&sv=1.0&sig=S2b_XQdlWwrHQqXk6VD9cPBpL_PFGumj03_eVPD7Eh0"

  # Create 'workitem.updated' hook for "Software Factory" projects (assigned/reassigned)
  python main.py --create-hooks-for-filtered-projects --filter-tag "Software Factory" --event-type workitem.updated --hook-url "https://prod-26.southcentralus.logic.azure.com:443/workflows/7a3968a93851401dabb3f01ba7d82ddf/triggers/Se_actualiza_un_work_item_asignado_o_se_reasigna_uno_existente/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2FSe_actualiza_un_work_item_asignado_o_se_reasigna_uno_existente%2Frun&sv=1.0&sig=2tiU0mGmHm-pDP1fKgZJz-TOBCXZcVkes7zlK87_zIM"

  # Create 'workitem.updated' hook for "Software Factory" projects (state update notification)
  python main.py --create-hooks-for-filtered-projects --filter-tag "Software Factory" --event-type workitem.updated --hook-url "https://prod-18.southcentralus.logic.azure.com:443/workflows/7e3259e5607740f28c50621158d7274e/triggers/Se_actualiza_el_estado_de_un_WI_y_notifica_al_creador/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2FSe_actualiza_el_estado_de_un_WI_y_notifica_al_creador%2Frun&sv=1.0&sig=Ygc6X0zNAqROkOCbBCKWGGmEXA_HVvoSvq9J0LYrUj8"
  ```
- **List and Upgrade Webhooks:** Finds projects by tag and updates their `workitem.updated` webhooks to use `resourceVersion: 1.0`.
  ```bash
  python main.py --list-and-upgrade-webhooks --filter-tag "Production"
  ```

- **Create Standard Hooks:** Creates a predefined set of three essential work item webhooks (created, updated-assigned, updated-state) for one or more projects.
  *Uses project IDs from `--project-id`, `--filter-tag`, or the `STANDARD_HOOK_PROJECT_IDS` environment variable (in that order of precedence).* 
  *If using the environment variable, ensure it's a comma-separated list (e.g., `id1,id2,id3`).*
  ```bash
  # Create standard hooks for a specific project (overrides .env)
  python main.py --create-standard-hooks --project-id <project_id>

  # Create standard hooks for all projects tagged with "Software Factory" (overrides .env)
  python main.py --create-standard-hooks --filter-tag "Software Factory"

  # Create standard hooks using project IDs defined in .env (STANDARD_HOOK_PROJECT_IDS)
  python main.py --create-standard-hooks
  ```

### Work Item Management (Requires `--project-id`)

- **List Work Items:**
  ```bash
  python main.py --list-work-items --project-id <project_id>
  ```
- **Create Work Item:**
  ```bash
  python main.py --create-work-item --project-id <project_id> --work-item-type "Task" --work-item-title "My New Task" --work-item-description "Details about the task."
  ```

### Advanced Work Item Querying & KPI Analytics

- **Dynamic Work Item Query with KPI Calculations:**
  ```bash
  # Query projects with user activity (smart filtering - efficient)
  python main.py --query-work-items --assigned-to "Carlos Vazquez,Alex Valenzuela"
  
  # Query ALL projects (no smart filtering - slower)
  python main.py --query-work-items --assigned-to "Carlos Vazquez,Alex Valenzuela" --all-projects
  
  # Query specific projects by name
  python main.py --query-work-items --project-names "ProjectA,ProjectB" --states "Closed,Done"
  
  # Query single project by ID
  python main.py --query-work-items --project-id <project_id> --start-date "2025-06-01" --end-date "2025-07-09"
  
  # Cross-project query with filters (smart filtering)
  python main.py --query-work-items --work-item-types "Task,User Story,Bug" --states "Closed,Done,Resolved" --start-date "2025-06-01" --assigned-to "Carlos Vazquez"
  
  # Query with area and iteration filters
  python main.py --query-work-items --project-id <project_id> --area-path "MyProject\\Development" --iteration-path "Sprint 1"
  
  # Export cross-project results to CSV (smart filtering)
  python main.py --query-work-items --export-csv "organization_work_items.csv" --assigned-to "Carlos Vazquez"
  
  # Skip efficiency calculations for faster results
  python main.py --query-work-items --no-efficiency --project-names "ProjectA,ProjectB"
  ```

**Project Scope Options:**
- `--project-id`: Query a specific project by ID
- `--project-names`: Query specific projects by name (comma-separated)
- *(No project args)*: Smart filtering - only query projects with user activity
- `--all-projects`: Query ALL projects (skip smart filtering for comprehensive results)

**Available Parameters:**
- `--assigned-to`: Comma-separated list of user names
- `--work-item-types`: Comma-separated list (Task, User Story, Bug, Feature, etc.)
- `--states`: Comma-separated list (Closed, Done, Active, In Progress, etc.)
- `--start-date` / `--end-date`: Date range in YYYY-MM-DD format
- `--date-field`: Field to use for date filtering (ClosedDate, StartDate, ChangedDate)
- `--area-path` / `--iteration-path`: Project structure filters
- `--no-efficiency`: Skip time efficiency calculations for faster results
- `--export-csv`: Export results to specified CSV file

**KPI Metrics Calculated:**
- On-time delivery percentage
- Average efficiency percentage (productive vs. total time)
- Total active and blocked hours
- State transition bottlenecks
- Individual work item efficiency metrics

### Other Project Operations (Requires `--project-id`)

- **List Connected GitHub Repositories:**
  ```bash
  python main.py --list-github-repos --project-id <project_id>
  ``` 