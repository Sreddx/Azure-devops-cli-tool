-- Simple Fabric Data Warehouse Query for Estimated Hours by Work Item IDs
-- Filters work items by the IDs provided in the JSON payload

SELECT
    WorkItemId,
    Title,
    WorkItemType,
    StartDate,
    TargetDate,
    AssignedToUser,
    AssignedToUserEmail,
    State,
    CreatedDate,
    AreaName,
    IterationName,
    EstimatedHours
FROM
    DevOps.workitems
WHERE
    WorkItemId IN (@WorkItemIds)
ORDER BY
    WorkItemId

-- The @WorkItemIds parameter will be populated from the JSON payload:
-- {"work_item_ids": ["12345", "12346", "12347"]}
-- Convert the array to comma-separated string: '12345,12346,12347'