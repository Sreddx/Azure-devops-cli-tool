# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Azure DevOps CLI tool written in Python that provides command-line interface for managing Azure DevOps projects, service hooks, work items, and KPI analytics. The tool allows cross-project queries and exports data to CSV for analysis.

## Project Structure

The project is organized into the following folders:

### `entry_points/`
- `main.py` - Main command-line interface entry point

### `classes/`
- `AzureDevOps.py` - Base class for Azure DevOps API authentication and HTTP requests
- `commands.py` - Extends AzureDevOps, implements project and service hook operations  
- `AzureDevopsProjectOperations.py` - Project-specific operations like work items and GitHub repos
- `WorkItemOperations.py` - Advanced work item querying, KPI calculations, and analytics
- `efficiency_calculator.py` - Fair efficiency metrics, delivery scoring, and business hours calculations
- `state_transition_stack.py` - Stack-based state transition tracking for accurate time measurement
- `project_discovery.py` - Efficient discovery of projects with user activity

### `config/`
- `config.py` - Configuration management using environment variables
- `config_loader.py` - JSON configuration file loading and validation
- `azure_devops_config.json` - Main configuration file with state categories, business hours, and scoring parameters

### `documentation/`
- `README.md` - Project overview and setup instructions
- `CLAUDE.md` - This file with project guidance
- `CONFIGURATION_USAGE.md` - Configuration system usage guide
- `WORK_ITEM_QUERYING_GUIDE.md` - Work item querying system documentation
- `FLOW_DIAGRAM.md` - System architecture and flow diagrams
- `IMPLEMENTATION_ANALYSIS.md` - Technical implementation details

## Dependencies and Setup

Install dependencies:
```bash
pip install -r requirements.txt
```

Required environment variables (create `.env` file):
```bash
AZURE_DEVOPS_ORG=<Your Azure DevOps Organization Name>
AZURE_DEVOPS_PAT=<Your Personal Access Token>
```

## Core Commands

Run the main tool:
```bash
python run.py <command> [options]
```

Get help and explanation of all commands:
```bash
python run.py --explain
```

Common operations:
- List projects: `python run.py --list-projects`
- Query work items: `python run.py --query-work-items --assigned-to "UserName"`
- Export to CSV: `python run.py --query-work-items --export-csv "results.csv"`

Alternatively, you can run directly:
```bash
python entry_points/main.py <command> [options]
```

## Architecture

### Core Classes

1. **AzureDevOps** (`classes/AzureDevOps.py`) - Base class handling Azure DevOps API authentication and HTTP requests
2. **AzureDevOpsCommands** (`classes/commands.py`) - Extends AzureDevOps, implements project and service hook operations
3. **AzureDevOpsProjectOperations** (`classes/AzureDevopsProjectOperations.py`) - Project-specific operations like work items and GitHub repos
4. **WorkItemOperations** (`classes/WorkItemOperations.py`) - Advanced work item querying, KPI calculations, and analytics
5. **EfficiencyCalculator** (`classes/efficiency_calculator.py`) - Fair efficiency metrics and delivery scoring with Mexico City timezone
6. **Config** (`config/config.py`) - Configuration management using environment variables
7. **ConfigLoader** (`config/config_loader.py`) - JSON configuration file loading and validation

### Request Flow

1. `entry_points/main.py` parses command line arguments using argparse
2. Creates appropriate operation class (Commands, ProjectOperations, or WorkItemOperations)
3. Operation classes inherit from base `AzureDevOps` class for authentication
4. HTTP requests made via `handle_request()` method with automatic error handling
5. Results processed and displayed, optionally exported to CSV

### Key Features

- **Smart Project Filtering**: Queries only projects with user activity for efficiency
- **KPI Analytics**: Calculates delivery scores, efficiency metrics, bottlenecks
- **CSV Export**: Enhanced exports with per-developer metrics and detailed work item data
- **Service Hook Management**: Create, list, upgrade webhooks across projects
- **Cross-Project Queries**: Query work items across multiple projects with filtering

### Work Item Query System

The work item querying supports multiple scopes:
- Single project (`--project-id`)
- Specific projects (`--project-names`) 
- Smart filtering (default - only projects with user activity)
- All projects (`--all-projects`)

Query filters include assignee, work item types, states, date ranges, area/iteration paths.

## Development Notes

- No formal testing framework detected - manual testing via CLI commands
- No linting configuration found - consider adding flake8/black for code quality
- Project uses environment-based configuration via python-dotenv
- API versioning handled through Config.API_VERSION dictionary
- Error handling implemented in base AzureDevOps.handle_request() method