# Azure DevOps Work Item Operations Flow Diagram

This document describes the step-by-step flow of how the Azure DevOps CLI tool processes work item queries and calculates KPIs.

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   main.py       │    │ WorkItemOps     │    │ Helper Modules  │
│                 │───▶│                 │───▶│                 │
│ • Parse CLI     │    │ • Orchestration │    │ • Efficiency    │
│ • Config setup  │    │ • Query builder │    │ • Discovery     │
│ • Delegation    │    │ • Results       │    │ • Export        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Detailed Flow

### 1. Initialization Phase

```
START: python main.py --query-work-items --assigned-to "User1,User2"

┌─────────────────────────────────────────────────────────────────┐
│ 1. main.py - Command Line Processing                           │
├─────────────────────────────────────────────────────────────────┤
│ • Parse command line arguments                                  │
│ • Load environment variables (.env file)                       │
│ • Build scoring configuration from:                            │
│   - JSON config file (--scoring-config)                       │
│   - Individual CLI parameters (--completion-bonus, etc.)      │
│ • Create WorkItemOperations instance with config              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. WorkItemOperations.__init__()                               │
├─────────────────────────────────────────────────────────────────┤
│ • Initialize Azure DevOps API client (base class)             │
│ • Create EfficiencyCalculator with scoring config             │
│ • Create ProjectDiscovery helper                              │
│ • Set up project caching                                      │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Project Discovery Phase

```
┌─────────────────────────────────────────────────────────────────┐
│ 3. Project Scope Determination                                 │
├─────────────────────────────────────────────────────────────────┤
│ IF --project-id specified:                                     │
│   └─▶ Query single project                                     │
│ ELIF --project-names specified:                                │
│   └─▶ Filter projects by name                                  │
│ ELIF --assigned-to AND NOT --all-projects:                     │
│   └─▶ Smart project discovery (find projects with activity)   │
│ ELSE:                                                          │
│   └─▶ Query ALL projects (warning shown)                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Smart Project Discovery (ProjectDiscovery module)           │
├─────────────────────────────────────────────────────────────────┤
│ • Check projects cache (projects_cache.json)                   │
│ • If cache fresh (< 24 hours): use cached projects            │
│ • If cache stale: fetch all projects from API                 │
│ • Build WIQL query conditions:                                │
│   - Users: [System.AssignedTo] IN ('User1', 'User2')         │
│   - Work item types (optional)                               │
│   - States (optional)                                        │
│   - Date ranges (optional)                                   │
│ • Test projects in batches of 20:                            │
│   - Execute test WIQL query per project                      │
│   - Skip projects with permission errors                     │
│   - Collect projects with matching work items                │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Work Item Query Phase

```
┌─────────────────────────────────────────────────────────────────┐
│ 5. WIQL Query Construction                                      │
├─────────────────────────────────────────────────────────────────┤
│ • Build comprehensive WIQL query:                              │
│   SELECT [System.Id], [System.Title], [System.AssignedTo],    │
│          [System.State], [System.WorkItemType],               │
│          [System.CreatedDate], [System.ChangedDate],          │
│          [Microsoft.VSTS.Scheduling.StartDate],               │
│          [Microsoft.VSTS.Scheduling.TargetDate],              │
│          [Microsoft.VSTS.Common.ClosedDate],                  │
│          [System.AreaPath], [System.IterationPath]            │
│   FROM WorkItems                                              │
│   WHERE [conditions based on filters]                         │
│ • Handle complex date filtering logic:                        │
│   - Closed items: use ClosedDate                             │
│   - Resolved items: use TargetDate                           │
│   - Active items: use TargetDate                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Query Execution Strategy                                     │
├─────────────────────────────────────────────────────────────────┤
│ TRY: Organization-level WIQL query (most efficient)            │
│ • Single API call across all projects                         │
│ • Automatic pagination handling                               │
│ • Extract work items with project context                     │
│                                                                │
│ FALLBACK: Project-by-project queries                          │
│ • Iterate through discovered projects                         │
│ • Execute WIQL query per project                              │
│ • Collect and merge results                                   │
│ • Skip projects with errors                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 4. Work Item Processing Phase

```
┌─────────────────────────────────────────────────────────────────┐
│ 7. Work Item Details Enrichment                                │
├─────────────────────────────────────────────────────────────────┤
│ For each work item found:                                       │
│ • Get work item details (batch API calls)                      │
│ • Extract core fields:                                         │
│   - Basic info: ID, title, assigned to, state, type          │
│   - Dates: created, changed, start, target, closed           │
│   - Structure: area path, iteration path                     │
│   - Project: project ID and name                             │
│ • Filter out items with unknown project IDs                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. Revision History Analysis                                    │
├─────────────────────────────────────────────────────────────────┤
│ For each work item (if efficiency calculation enabled):        │
│ • Fetch revision history via API                              │
│ • Extract state transitions:                                   │
│   - Revision number, state, changed date, changed by         │
│   - Reason for change                                         │
│ • Build chronological state history                           │
│ • Display first 10 items with revision details for review     │
└─────────────────────────────────────────────────────────────────┘
```

### 5. Efficiency Calculation Phase

```
┌─────────────────────────────────────────────────────────────────┐
│ 9. Efficiency Metrics (EfficiencyCalculator module)            │
├─────────────────────────────────────────────────────────────────┤
│ For each work item:                                             │
│ A. State Time Analysis:                                        │
│    • Calculate time between state transitions                  │
│    • For productive states: count business hours only         │
│      (Monday-Friday, max 10 hours/day configurable)          │
│    • For blocked states: count total time                     │
│    • Detect reopened items (Closed → Active pattern)         │
│                                                                │
│ B. Estimated Time Calculation:                                │
│    • Primary: start_date to target_date (business hours)      │
│    • Fallback: work item type defaults                       │
│      - User Story: 16 hours, Task: 8 hours, Bug: 4 hours    │
│                                                                │
│ C. Delivery Timing Analysis:                                  │
│    • Compare closed_date vs target_date                       │
│    • Early delivery bonuses:                                  │
│      - Very early (7+ days): 130% score + 1.0h/day bonus    │
│      - Early (3-7 days): 120% score + 0.5h/day bonus        │
│      - Slightly early (1-3 days): 110% + 0.25h/day bonus    │
│    • Late delivery penalties:                                 │
│      - 1-3 days late: 90% score + 2h mitigation             │
│      - 4-7 days late: 80% score + 4h mitigation             │
│      - 8-14 days late: 70% score + 6h mitigation            │
│      - 15+ days late: 60% score + 8h mitigation             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 10. Fair Efficiency Score Calculation                          │
├─────────────────────────────────────────────────────────────────┤
│ For each work item:                                             │
│ • Completion bonus = 20% of estimated time (if completed)      │
│ • Numerator = active_hours + completion_bonus + timing_bonus   │
│ • Denominator = estimated_hours + late_penalty_mitigation      │
│ • Fair efficiency = (numerator / denominator) × 100           │
│ • Cap at 150% maximum                                          │
│ • Traditional efficiency = active_hours / total_hours × 100    │
└─────────────────────────────────────────────────────────────────┘
```

### 6. KPI Aggregation Phase

```
┌─────────────────────────────────────────────────────────────────┐
│ 11. Per-Developer Metrics Calculation                          │
├─────────────────────────────────────────────────────────────────┤
│ Group work items by assigned developer:                        │
│ For each developer:                                             │
│ • Basic counts: total items, completed items, completion rate  │
│ • Efficiency metrics: avg fair efficiency, avg delivery score  │
│ • Timing analysis: early/on-time/late delivery breakdown      │
│ • Reopened items handling count and rate                      │
│ • Active hours total and estimated hours total                │
│ • Work item types variety and projects worked on              │
│ • Overall developer score calculation:                        │
│   Score = (fair_efficiency × 0.4) + (delivery_score × 0.3) +  │
│           (completion_rate × 0.2) + (on_time_delivery × 0.1)  │
│   (All weights are configurable)                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 12. Bottleneck Analysis                                         │
├─────────────────────────────────────────────────────────────────┤
│ • Aggregate time spent in each state across all work items     │
│ • Calculate average time per state                             │
│ • Rank states by average time (identify bottlenecks)          │
│ • Return top 5 states with highest average time               │
└─────────────────────────────────────────────────────────────────┘
```

### 7. Output Phase

```
┌─────────────────────────────────────────────────────────────────┐
│ 13. Results Display                                             │
├─────────────────────────────────────────────────────────────────┤
│ • Query summary: scope, total items, projects queried          │
│ • Filters applied summary                                       │
│ • Overall summary: total developers, avg metrics               │
│ • Per-developer detailed metrics:                              │
│   - Work items count and completion rate                      │
│   - Fair efficiency and delivery scores                       │
│   - Overall developer score                                   │
│   - Active hours and timing metrics                           │
│   - Delivery timing breakdown                                 │
│ • Top bottlenecks by state                                    │
│ • Sample work items with efficiency details                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ 14. CSV Export (Optional)                                       │
├─────────────────────────────────────────────────────────────────┤
│ If --export-csv specified:                                     │
│ • Generate detailed work items CSV:                            │
│   - All work item details and efficiency metrics              │
│   - File: {base_filename}_detailed.csv                        │
│ • Generate developer summary CSV:                             │
│   - Per-developer KPI metrics                                 │
│   - Delivery timing breakdown                                 │
│   - File: {base_filename}_developer_summary.csv               │
└─────────────────────────────────────────────────────────────────┘
```

## Configuration Options

### Scoring Configuration

Users can customize scoring parameters via:

1. **JSON Configuration File** (`--scoring-config path/to/config.json`):
```json
{
  "completion_bonus_percentage": 0.25,
  "max_efficiency_cap": 200.0,
  "max_hours_per_day": 12.0,
  "developer_score_weights": {
    "fair_efficiency": 0.5,
    "delivery_score": 0.3,
    "completion_rate": 0.1,
    "on_time_delivery": 0.1
  },
  "early_delivery_scores": {
    "very_early": 140.0,
    "early": 125.0
  }
}
```

2. **Individual CLI Parameters**:
- `--completion-bonus 0.25` (25% completion bonus)
- `--max-efficiency-cap 200.0` (200% efficiency cap)
- `--fair-efficiency-weight 0.5` (50% weight for fair efficiency)
- `--delivery-score-weight 0.3` (30% weight for delivery score)

### Performance Optimizations

1. **Project Caching**: Projects are cached for 24 hours to avoid repeated API calls
2. **Smart Discovery**: Only checks projects with user activity (unless `--all-projects`)
3. **Batch Processing**: Work item details fetched in batches of 200
4. **Pagination**: Automatic handling of large result sets
5. **Business Hours**: Only productive time counted during weekdays

### Error Handling

- Projects with permission errors are skipped gracefully
- Fallback strategies for different query approaches
- Invalid date handling with sensible defaults
- Cache corruption recovery with fresh API calls

## Key Benefits of Optimized Architecture

1. **Modularity**: Separate concerns (discovery, calculation, export)
2. **Configurability**: Scoring parameters can be customized per organization
3. **Performance**: Smart caching and efficient project discovery
4. **Maintainability**: Clean separation of responsibilities
5. **Extensibility**: Easy to add new efficiency metrics or export formats