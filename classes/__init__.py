"""
Azure DevOps CLI tool classes package.
Contains core functionality classes for Azure DevOps operations.
"""

from .AzureDevOps import AzureDevOps
from .commands import AzureDevOpsCommands
from .AzureDevopsProjectOperations import AzureDevOpsProjectOperations
from .WorkItemOperations import WorkItemOperations
from .efficiency_calculator import EfficiencyCalculator
from .state_transition_stack import WorkItemStateStack, create_stack_from_work_item
from .project_discovery import ProjectDiscovery

__all__ = [
    'AzureDevOps',
    'AzureDevOpsCommands',
    'AzureDevOpsProjectOperations', 
    'WorkItemOperations',
    'EfficiencyCalculator',
    'WorkItemStateStack',
    'create_stack_from_work_item',
    'ProjectDiscovery'
]