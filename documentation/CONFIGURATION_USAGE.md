# Configuration Usage Guide

## Overview

The Azure DevOps CLI tool now uses a comprehensive JSON configuration file (`azure_devops_config.json`) that allows you to customize:

- Which states to fetch from Azure DevOps
- State categories (productive, pause/stopper, completion, ignored)
- Business hours and office configuration
- Efficiency scoring parameters
- Developer scoring weights

## Configuration File Structure

### Complete Example Configuration

```json
{
  "work_item_query": {
    "states_to_fetch": [
      "New", "Active", "In Progress", "Development", 
      "Code Review", "Testing", "Resolved", "Closed", 
      "Done", "Stopper", "Blocked", "On Hold", "Waiting"
    ],
    "work_item_types": ["Task", "User Story", "Bug", "Feature"],
    "date_field": "ClosedDate",
    "include_active_items": true,
    "smart_filtering": true
  },
  "state_categories": {
    "assigned_states": ["New"],
    "productive_states": ["Active", "In Progress", "Development", "Code Review", "Testing"],
    "pause_stopper_states": ["Stopper", "Blocked", "On Hold", "Waiting"],
    "completion_states": ["Resolved", "Closed", "Done"],
    "ignored_states": ["Removed", "Discarded", "Cancelled"]
  },
  "business_hours": {
    "office_start_hour": 9,
    "office_end_hour": 17,
    "max_hours_per_day": 8,
    "timezone": "UTC"
  },
  "efficiency_scoring": {
    "completion_bonus_percentage": 0.20,
    "max_efficiency_cap": 150.0
  },
  "developer_scoring": {
    "weights": {
      "fair_efficiency": 0.4,
      "delivery_score": 0.3,
      "completion_rate": 0.2,
      "on_time_delivery": 0.1
    }
  }
}
```

## State Categories Behavior

### 1. **Assigned States** (`New`)
- **Behavior**: Work items with start/target dates within query timeframe count as assigned tasks
- **Time Tracking**: No time counted toward efficiency (assignment state)
- **Example**: A `New` task with target date within your query range will be included

### 2. **Productive States** (`Active`, `In Progress`, `Development`, `Code Review`, `Testing`)
- **Behavior**: Time spent in these states counts toward efficiency metrics
- **Time Tracking**: Business hours only (8 hours max per day, weekdays only)
- **Efficiency Impact**: Contributes to fair efficiency score calculation

### 3. **Pause/Stopper States** (`Stopper`, `Blocked`, `On Hold`, `Waiting`)
- **Behavior**: Pauses time tracking - doesn't count toward efficiency
- **Time Tracking**: Tracked separately as "paused time"
- **Efficiency Impact**: Does not hurt efficiency scores
- **Use Case**: When work is blocked by external dependencies

### 4. **Completion States** (`Resolved`, `Closed`, `Done`)
- **Behavior**: Stops time accumulation, eligible for completion bonus
- **Time Tracking**: Marks end of work item lifecycle
- **Efficiency Impact**: Triggers completion bonus (20% of estimated time)

### 5. **Ignored States** (`Removed`, `Discarded`, `Cancelled`)
- **Behavior**: Work items are completely excluded from analysis
- **Time Tracking**: No time tracking
- **Efficiency Impact**: Not included in any calculations

## Usage Examples

### Basic Usage with Default Configuration

```bash
# Uses azure_devops_config.json automatically
python main.py --query-work-items \
  --assigned-to "Carlos Vazquez,Diego Lopez" \
  --start-date "2025-08-01" \
  --end-date "2025-08-21"
```

### Using Custom Configuration File

```bash
# Use your custom config file
python main.py --query-work-items \
  --scoring-config "my_custom_config.json" \
  --assigned-to "Carlos Vazquez" \
  --export-csv "carlos_analysis"
```

### Override Configuration via CLI

```bash
# Override specific settings via command line
python main.py --query-work-items \
  --assigned-to "Carlos Vazquez" \
  --completion-bonus 0.25 \
  --max-efficiency-cap 120.0 \
  --max-hours-per-day 6 \
  --fair-efficiency-weight 0.5
```

## Customization Examples

### Example 1: Different Office Hours
```json
{
  "business_hours": {
    "office_start_hour": 8,
    "office_end_hour": 18,
    "max_hours_per_day": 10,
    "timezone": "America/Mexico_City"
  }
}
```

### Example 2: Custom State Categories
```json
{
  "state_categories": {
    "assigned_states": ["New", "Approved"],
    "productive_states": ["Active", "In Progress", "Development", "Code Review", "Testing", "Validation"],
    "pause_stopper_states": ["Blocked", "Waiting for Approval", "External Dependency"],
    "completion_states": ["Done", "Closed", "Deployed"],
    "ignored_states": ["Cancelled", "Duplicate", "Won't Fix"]
  }
}
```

### Example 3: Adjusted Scoring Weights
```json
{
  "developer_scoring": {
    "weights": {
      "fair_efficiency": 0.5,
      "delivery_score": 0.25,
      "completion_rate": 0.15,
      "on_time_delivery": 0.1
    }
  }
}
```

## State Flow Logic

```
New (assigned) → Active (productive) → Blocked (paused) → Active (productive) → Resolved (completed)
```

**Time Calculation**:
1. `New`: 0 hours counted (assignment state)
2. `Active`: Business hours counted toward efficiency
3. `Blocked`: Hours tracked as "paused time", not counted against efficiency
4. `Active` (resumed): Business hours counted toward efficiency again
5. `Resolved`: Work item completed, eligible for completion bonus

## Advanced Configuration

### Debugging Settings
```json
{
  "debugging": {
    "show_state_transitions": true,
    "show_time_calculations": true,
    "show_ignored_items": true,
    "max_debug_items": 10
  }
}
```

### Export Customization
```json
{
  "export_settings": {
    "detailed_csv_fields": [
      "ID", "Title", "Assigned To", "State", 
      "Active Time (Hours)", "Paused Time (Hours)",
      "Fair Efficiency Score", "Delivery Score"
    ]
  }
}
```

## Migration from Previous Version

If you were using the previous system with CLI arguments, here's how to migrate:

**Old Way**:
```bash
python main.py --query-work-items \
  --productive-states "Active,In Progress,Development" \
  --blocked-states "Blocked,On Hold"
```

**New Way** - Create config file:
```json
{
  "state_categories": {
    "productive_states": ["Active", "In Progress", "Development"],
    "pause_stopper_states": ["Blocked", "On Hold"]
  }
}
```

Then run:
```bash
python main.py --query-work-items --scoring-config "my_config.json"
```

## Configuration Validation

The system automatically validates your configuration and adds missing default values. If you have an invalid configuration file, it will:

1. Show warning messages about invalid/missing sections
2. Use default values for missing configuration
3. Continue execution with merged configuration

## Testing Your Configuration

To test your configuration, run with debug output:

```bash
python main.py --query-work-items \
  --assigned-to "TestUser" \
  --start-date "2025-08-01" \
  --end-date "2025-08-02"
```

The tool will display:
- Configuration file being used
- States being fetched
- State categories being applied
- Filtered/ignored work items

This ensures your configuration is working as expected before running larger analyses.