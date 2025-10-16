"""
Configuration loader for Azure DevOps work item analysis.
Handles loading and validation of JSON configuration files.
"""

import json
import os
from typing import Dict, List, Optional, Any


class ConfigLoader:
    """Loads and validates Azure DevOps analysis configuration."""
    
    def __init__(self, config_file_path: str = None):
        """
        Initialize configuration loader.
        
        Args:
            config_file_path: Path to the JSON configuration file
        """
        # Set default config file path relative to this file
        if config_file_path is None:
            config_file_path = os.path.join(os.path.dirname(__file__), "azure_devops_config.json")
        self.config_file_path = config_file_path
        self.config = {}
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        if not os.path.exists(self.config_file_path):
            print(f"Configuration file {self.config_file_path} not found. Using defaults.")
            self.config = self._get_default_config()
            return self.config
        
        try:
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print(f"Loaded configuration from {self.config_file_path}")
            self._validate_config()
            print("CONFIGURACION CARGADA")
            return self.config
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading config file: {e}. Using defaults.")
            self.config = self._get_default_config()
            return self.config
    
    def _validate_config(self):
        """Validate loaded configuration and add defaults for missing keys."""
        default_config = self._get_default_config()
        
        # Ensure all required sections exist
        for section_key, section_value in default_config.items():
            if section_key not in self.config:
                self.config[section_key] = section_value
                print(f"Added missing config section: {section_key}")
            elif isinstance(section_value, dict):
                # Validate nested dictionaries
                for key, value in section_value.items():
                    if key not in self.config[section_key]:
                        self.config[section_key][key] = value
                        print(f"Added missing config key: {section_key}.{key}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "work_item_query": {
                "states_to_fetch": ["New", "Active", "In Progress", "Resolved", "Closed", "Done"],
                "work_item_types": ["Task", "User Story", "Bug", "Feature"],
                "date_field": "ClosedDate",
                "include_active_items": True,
                "smart_filtering": True
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
                "timezone": "America/Mexico_City",
                "working_days": [1, 2, 3, 4, 5]
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
    
    def get_states_to_fetch(self) -> List[str]:
        """Get list of states to fetch from Azure DevOps."""
        return self.config.get("work_item_query", {}).get("states_to_fetch", [])
    
    def get_work_item_types(self) -> List[str]:
        """Get list of work item types to fetch."""
        return self.config.get("work_item_query", {}).get("work_item_types", [])
    
    def get_state_categories(self) -> Dict[str, List[str]]:
        """Get state categories configuration."""
        return self.config.get("state_categories", {})
    
    def get_assigned_states(self) -> List[str]:
        """Get states considered as assigned."""
        return self.config.get("state_categories", {}).get("assigned_states", [])
    
    def get_productive_states(self) -> List[str]:
        """Get states considered productive."""
        return self.config.get("state_categories", {}).get("productive_states", [])
    
    def get_pause_stopper_states(self) -> List[str]:
        """Get states that pause time tracking."""
        return self.config.get("state_categories", {}).get("pause_stopper_states", [])
    
    def get_completion_states(self) -> List[str]:
        """Get states that indicate completion."""
        return self.config.get("state_categories", {}).get("completion_states", [])
    
    def get_ignored_states(self) -> List[str]:
        """Get states that should be ignored from analysis."""
        return self.config.get("state_categories", {}).get("ignored_states", [])
    
    def get_business_hours_config(self) -> Dict[str, Any]:
        """Get business hours configuration."""
        return self.config.get("business_hours", {})
    
    def get_efficiency_scoring_config(self) -> Dict[str, Any]:
        """Get efficiency scoring configuration."""
        return self.config.get("efficiency_scoring", {})
    
    def get_developer_scoring_config(self) -> Dict[str, Any]:
        """Get developer scoring configuration."""
        return self.config.get("developer_scoring", {})
    
    def should_include_work_item(self, work_item: Dict[str, Any]) -> bool:
        """
        Check if a work item should be included in analysis based on its current state.
        
        Args:
            work_item: Work item data
            
        Returns:
            True if work item should be included, False if it should be ignored
        """
        current_state = work_item.get('state', '')
        ignored_states = self.get_ignored_states()
        
        # Check if current state is in ignored states
        return current_state not in ignored_states
    
    def should_include_work_item_with_history(self, work_item: Dict[str, Any], 
                                            state_history: List[Dict]) -> bool:
        """
        Check if a work item should be included based on its state history.
        
        Args:
            work_item: Work item data
            state_history: List of state transitions
            
        Returns:
            True if work item should be included, False if ignored
        """
        # Check current state
        if not self.should_include_work_item(work_item):
            return False
        
        # Check if work item has ever been in ignored states
        ignored_states = self.get_ignored_states()
        for revision in state_history:
            if revision.get('state', '') in ignored_states:
                return False
        
        return True
    
    def get_date_range_filter_for_assigned_items(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get filter configuration for assigned items (New state) within date range.
        
        Args:
            start_date: Start date string
            end_date: End date string
            
        Returns:
            Filter configuration for assigned items
        """
        transition_config = self.config.get("state_transitions", {}).get("assigned_condition", {})
        
        return {
            "states": self.get_assigned_states(),
            "requires_date_check": transition_config.get("requires_date_in_range", True),
            "date_fields": transition_config.get("date_fields_to_check", ["start_date", "target_date"]),
            "start_date": start_date,
            "end_date": end_date
        }
    
    def update_config_from_cli_args(self, args) -> None:
        """
        Update configuration with command line arguments.
        
        Args:
            args: Parsed command line arguments
        """
        # Update efficiency scoring from CLI args
        if hasattr(args, 'completion_bonus') and args.completion_bonus is not None:
            self.config.setdefault("efficiency_scoring", {})["completion_bonus_percentage"] = args.completion_bonus
        
        if hasattr(args, 'max_efficiency_cap') and args.max_efficiency_cap is not None:
            self.config.setdefault("efficiency_scoring", {})["max_efficiency_cap"] = args.max_efficiency_cap
        
        # Update business hours from CLI args
        if hasattr(args, 'max_hours_per_day') and args.max_hours_per_day is not None:
            self.config.setdefault("business_hours", {})["max_hours_per_day"] = args.max_hours_per_day
        
        # Update developer scoring weights from CLI args
        if any(hasattr(args, attr) and getattr(args, attr) is not None for attr in [
            'fair_efficiency_weight', 'delivery_score_weight', 'completion_rate_weight', 'on_time_delivery_weight'
        ]):
            weights = self.config.setdefault("developer_scoring", {}).setdefault("weights", {})
            
            if hasattr(args, 'fair_efficiency_weight') and args.fair_efficiency_weight is not None:
                weights["fair_efficiency"] = args.fair_efficiency_weight
            if hasattr(args, 'delivery_score_weight') and args.delivery_score_weight is not None:
                weights["delivery_score"] = args.delivery_score_weight
            if hasattr(args, 'completion_rate_weight') and args.completion_rate_weight is not None:
                weights["completion_rate"] = args.completion_rate_weight
            if hasattr(args, 'on_time_delivery_weight') and args.on_time_delivery_weight is not None:
                weights["on_time_delivery"] = args.on_time_delivery_weight
        
        # Update state lists from CLI args  
        if hasattr(args, 'productive_states') and args.productive_states:
            productive_states = [s.strip() for s in args.productive_states.split(',')]
            self.config.setdefault("state_categories", {})["productive_states"] = productive_states
        
        if hasattr(args, 'blocked_states') and args.blocked_states:
            blocked_states = [s.strip() for s in args.blocked_states.split(',')]
            self.config.setdefault("state_categories", {})["pause_stopper_states"] = blocked_states