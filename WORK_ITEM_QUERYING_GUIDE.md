# Work Item Querying & KPI Analytics Guide

## Overview

This guide covers the advanced work item querying capabilities that have been integrated into your Azure DevOps CLI tool. The new functionality allows you to:

- Query work items with dynamic, flexible filtering
- **Cross-project querying**: Query across all projects or specific projects
- Calculate time efficiency KPIs and metrics
- Analyze productivity bottlenecks
- Export results to CSV for further analysis
- Track historic work item revisions

## Cross-Project Querying

The work item querying functionality supports three different scopes:

1. **Organization-wide**: Query ALL projects in your organization
2. **Multi-project**: Query specific projects by name
3. **Single project**: Query one specific project by ID

This makes it perfect for:
- **Organization-wide analytics**: Get insights across all your projects
- **Team productivity analysis**: Track specific teams across multiple projects
- **Resource allocation**: See where developers are spending time across projects
- **Cross-project reporting**: Generate comprehensive reports for management

## Architecture

The work item querying functionality is implemented in `WorkItemOperations.py` and follows the same patterns as the existing codebase:

- **WorkItemOperations class**: Extends `AzureDevOps` base class
- **Dynamic WIQL Query Builder**: Constructs queries based on parameters
- **KPI Calculation Engine**: Analyzes time efficiency and productivity metrics
- **CSV Export**: Structured data export for reporting

## API Endpoints Used

1. **WIQL Query**: `POST /_apis/wit/wiql?api-version=7.0`
2. **Work Item Details**: `GET /_apis/wit/workitems?ids={ids}&api-version=7.1`
3. **Work Item Revisions**: `GET /_apis/wit/workitems/{id}/revisions?api-version=7.1`

## Command Reference

### Basic Usage

```bash
# Query all closed work items across ALL projects
python main.py --query-work-items

# Query specific project by ID
python main.py --query-work-items --project-id <project_id>

# Query specific projects by name
python main.py --query-work-items --project-names "ProjectA,ProjectB"
```

### Cross-Project Querying

```bash
# Query all projects for specific developers
python main.py --query-work-items --assigned-to "Carlos Vazquez,Alex Valenzuela"

# Query specific projects with filters
python main.py --query-work-items --project-names "ProjectA,ProjectB" --work-item-types "Task,User Story,Bug" --states "Closed,Done,Resolved"

# Organization-wide date range filtering
python main.py --query-work-items --start-date "2025-06-01" --end-date "2025-07-09"

# Cross-project export
python main.py --query-work-items --export-csv "organization_metrics.csv" --assigned-to "Carlos Vazquez"
```

### Single Project Filtering

```bash
# Query by specific developers in one project
python main.py --query-work-items --project-id <project_id> --assigned-to "Carlos Vazquez,Alex Valenzuela"

# Query specific work item types and states in one project
python main.py --query-work-items --project-id <project_id> --work-item-types "Task,User Story,Bug" --states "Closed,Done,Resolved"

# Use different date fields
python main.py --query-work-items --project-id <project_id> --date-field "StartDate" --start-date "2025-06-01"

# Area and iteration path filtering
python main.py --query-work-items --project-id <project_id> --area-path "MyProject\\Development" --iteration-path "Sprint 1"
```

### Performance & Export Options

```bash
# Skip efficiency calculations for faster results (cross-project)
python main.py --query-work-items --no-efficiency --project-names "ProjectA,ProjectB"

# Export results to CSV (single project)
python main.py --query-work-items --project-id <project_id> --export-csv "work_items_report.csv"

# Organization-wide export
python main.py --query-work-items --export-csv "organization_analysis.csv" --start-date "2025-06-01"
```

### Complete Examples

```bash
# Organization-wide comprehensive query
python main.py --query-work-items \
  --assigned-to "Carlos Vazquez,Alex Valenzuela" \
  --work-item-types "Task,User Story,Bug" \
  --states "Closed,Done" \
  --start-date "2025-06-01" \
  --end-date "2025-07-09" \
  --date-field "ClosedDate" \
  --export-csv "organization_sprint_analysis.csv"

# Specific projects query
python main.py --query-work-items \
  --project-names "ProjectA,ProjectB" \
  --assigned-to "Carlos Vazquez,Alex Valenzuela" \
  --work-item-types "Task,User Story,Bug" \
  --states "Closed,Done" \
  --start-date "2025-06-01" \
  --end-date "2025-07-09" \
  --export-csv "multi_project_analysis.csv"

# Single project with area/iteration filters
python main.py --query-work-items \
  --project-id <project_id> \
  --assigned-to "Carlos Vazquez,Alex Valenzuela" \
  --work-item-types "Task,User Story,Bug" \
  --states "Closed,Done" \
  --start-date "2025-06-01" \
  --end-date "2025-07-09" \
  --date-field "ClosedDate" \
  --area-path "MyProject\\Development" \
  --export-csv "sprint_analysis.csv"
```

## KPI Metrics Calculated

### Individual Work Item Metrics
- **Active Time**: Time spent in productive states
- **Blocked Time**: Time spent in blocked/waiting states
- **Efficiency Percentage**: (Active Time / Total Time) × 100
- **State Breakdown**: Time spent in each state

### Project-Level KPIs
- **On-time Delivery Percentage**: Work items completed by target date
- **Average Efficiency**: Mean efficiency across all work items
- **Total Active/Blocked Hours**: Aggregate time metrics
- **Bottleneck Analysis**: States with highest average time

### Productive vs Blocked States

**Default Productive States:**
- Active
- In Progress
- Code Review
- Testing

**Default Blocked States:**
- Blocked
- Waiting
- On Hold

## Output Example

```
================================================================================
WORK ITEMS QUERY RESULTS
================================================================================
Total items found: 25
Assigned to: Carlos Vazquez, Alex Valenzuela
Work item types: Task, User Story, Bug
States: Closed, Done
Date range: 2025-06-01 to 2025-07-09

KPI SUMMARY:
  On-time delivery: 72.0%
  Average efficiency: 68.5%
  Total active hours: 340.5
  Total blocked hours: 89.2

TOP BOTTLENECKS:
  1. Code Review: 12.5h avg (8 occurrences)
  2. Waiting: 8.3h avg (5 occurrences)
  3. Blocked: 6.7h avg (3 occurrences)

WORK ITEMS SUMMARY:
  ID 1234: Implement user authentication system...
    Assigned: Carlos Vazquez | State: Done
    Efficiency: 75.2% | Active: 28.5h

  ID 1235: Fix login validation bug...
    Assigned: Alex Valenzuela | State: Closed
    Efficiency: 82.1% | Active: 15.3h
...
================================================================================
```

## CSV Export Format

The exported CSV includes the following columns:

- **ID**: Work item ID
- **Title**: Work item title
- **Project Name**: Name of the project (useful for cross-project queries)
- **Assigned To**: Current assignee
- **State**: Current state
- **Work Item Type**: Task, User Story, Bug, etc.
- **Created Date**: When the work item was created
- **Closed Date**: When the work item was closed
- **Target Date**: Planned completion date
- **Active Time (Hours)**: Time in productive states
- **Blocked Time (Hours)**: Time in blocked states
- **Efficiency %**: Calculated efficiency percentage

## Integration with Existing CLI

The work item querying functionality seamlessly integrates with the existing CLI structure:

1. **Follows existing patterns**: Uses same base classes and error handling
2. **Consistent configuration**: Uses existing config.py for API versions
3. **Unified help system**: Integrated into --help and --explain commands
4. **Same authentication**: Uses existing PAT and organization settings

## Error Handling

The implementation includes comprehensive error handling:

- **API Errors**: Handled by base `AzureDevOps` class
- **Invalid Dates**: Gracefully skipped with warnings
- **Missing Data**: Default values and safe fallbacks
- **CSV Export Errors**: Detailed error messages

## Performance Considerations

- **Efficiency Calculations**: Can be skipped with `--no-efficiency` for faster results
- **Batch API Calls**: Work item details fetched in batches
- **Memory Management**: Streaming CSV export for large datasets
- **API Rate Limits**: Uses existing request handling with proper error management

## Best Practices

1. **Use date ranges**: Always specify reasonable date ranges to avoid large datasets
2. **Filter appropriately**: Use specific filters (assigned-to, states) to narrow results
3. **Skip efficiency when not needed**: Use `--no-efficiency` for quick queries
4. **Export large datasets**: Use CSV export for analysis in Excel/other tools
5. **Monitor API usage**: Be mindful of Azure DevOps API rate limits

## Troubleshooting

**Common Issues:**

1. **No results returned**: Check if filters are too restrictive
2. **Performance slow**: Use `--no-efficiency` or narrow date ranges
3. **Authentication errors**: Verify PAT has work item read permissions
4. **Date parsing errors**: Ensure dates are in YYYY-MM-DD format

**Required Permissions:**
- Work Items: Read
- Projects: Read
- Analytics: Read (for revision history)

## Future Enhancements

Potential areas for future development:

1. **Custom productive states**: Allow configuration of what states are considered productive
2. **Team-level metrics**: Aggregate KPIs by team or area path
3. **Historical trending**: Compare KPIs across different time periods
4. **Burndown charts**: Generate sprint/iteration burndown data
5. **Integration with Power BI**: Direct export to Power BI datasets