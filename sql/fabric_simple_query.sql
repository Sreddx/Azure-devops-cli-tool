-- Simple version: Just get estimated hours for specific work item IDs
-- Use this if you only need the basic data

SELECT
    WorkItemId,
    EstimatedHours
FROM
    DevOps.workitems
WHERE
    WorkItemId IN (@WorkItemIds)
ORDER BY
    WorkItemId

-- Parameters:
-- @WorkItemIds: Comma-separated string like '12345,12346,12347'