"""
Efficiency calculation module for Azure DevOps work items.
Handles fair efficiency metrics, delivery scoring, and business hours calculations.
Uses stack-based state transition tracking for accurate time measurement.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from classes.state_transition_stack import WorkItemStateStack, create_stack_from_work_item


class EfficiencyCalculator:
    """Calculator for work item efficiency metrics and developer scoring."""
    
    def __init__(self, scoring_config: Optional[Dict] = None):
        """
        Initialize with configurable scoring parameters.
        
        Args:
            scoring_config: Dictionary with scoring configuration parameters
        """
        # Default scoring configuration
        self.config = {
            'completion_bonus_percentage': 0.20,  # 20% of estimated time
            'max_efficiency_cap': 150.0,  # Cap efficiency at 150%
            'max_hours_per_day': 8.0,   # Maximum business hours per day (changed from 10)
            'early_delivery_thresholds': {
                'very_early_days': 7,
                'early_days': 3,
                'slightly_early_days': 1
            },
            'early_delivery_scores': {
                'very_early': 130.0,
                'early': 120.0,
                'slightly_early': 110.0,
                'on_time': 100.0
            },
            'early_delivery_bonuses': {
                'very_early': 1.0,  # hours per day early
                'early': 0.5,
                'slightly_early': 0.25
            },
            'late_delivery_scores': {
                'late_1_3': 90.0,
                'late_4_7': 80.0,
                'late_8_14': 70.0,
                'late_15_plus': 60.0
            },
            'late_penalty_mitigation': {
                'late_1_3': 2.0,
                'late_4_7': 4.0,
                'late_8_14': 6.0,
                'late_15_plus': 8.0
            },
            'developer_score_weights': {
                'fair_efficiency': 0.4,    # 40%
                'delivery_score': 0.3,     # 30%
                'completion_rate': 0.2,    # 20%
                'on_time_delivery': 0.1    # 10%
            },
            'default_work_item_hours': {
                'user story': 8.0,   # 1 day (reduced from 16)
                'task': 4.0,         # 0.5 day (reduced from 8) 
                'bug': 2.0,          # 0.25 day (reduced from 4)
                'default': 4.0       # 0.5 day (reduced from 8)
            }
        }
        
        # Update with user-provided configuration
        if scoring_config:
            self._update_config(scoring_config)
    
    def _update_config(self, user_config: Dict):
        """Recursively update configuration with user values."""
        def merge_dicts(base_dict, update_dict):
            for key, value in update_dict.items():
                if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                    merge_dicts(base_dict[key], value)
                else:
                    base_dict[key] = value
        
        merge_dicts(self.config, user_config)
    
    def calculate_fair_efficiency_metrics(self, 
                                        work_item: Dict,
                                        state_history: List[Dict], 
                                        state_config: Optional[Dict] = None) -> Dict:
        """
        Calculate fair efficiency metrics using stack-based state transition tracking with state categories.
        
        Args:
            work_item: Work item details with dates and metadata
            state_history: List of state changes with timestamps
            state_config: Configuration for state categories and behaviors
        Returns:
            Dictionary with enhanced efficiency metrics
        """
        if len(state_history) < 2:
            return self._empty_efficiency_metrics()
        
        # Use provided state config or defaults
        if state_config is None:
            state_config = {
                'productive_states': ['Active', 'In Progress', 'Development', 'Code Review', 'Testing'],
                'pause_stopper_states': ['Stopper', 'Blocked', 'On Hold', 'Waiting'],
                'completion_states': ['Resolved', 'Closed', 'Done'],
                'ignored_states': ['Removed', 'Discarded', 'Cancelled']
            }
        
        # Create stack-based state tracker with office hours configuration
        office_hours_config = {
            'office_start_hour': self.config.get('office_start_hour', 9),
            'office_end_hour': self.config.get('office_end_hour', 17),
            'max_hours_per_day': self.config.get('max_hours_per_day', 8),
            'timezone_str': self.config.get('timezone', 'America/Mexico_City')
        }
        
        state_stack = create_stack_from_work_item(
            work_item, state_history, state_config, office_hours_config
        )
        
        # Check if work item should be ignored
        if state_stack.should_ignore_work_item():
            return self._ignored_work_item_metrics()
        
        # Get time metrics from stack
        productive_hours = state_stack.get_total_productive_hours()
        paused_hours = state_stack.get_total_paused_hours()
        total_hours = state_stack.get_total_time_all_states()
        state_durations = state_stack.get_state_durations()
        pattern_summary = state_stack.get_pattern_summary()
        
        # Calculate estimated time from OriginalEstimate field
        estimated_hours = self._calculate_estimated_time_from_work_item(work_item)
        
        # Calculate delivery timing
        delivery_metrics = self._calculate_delivery_timing(work_item)
        
        # Calculate completion bonus
        is_completed = work_item.get('state', '').lower() in ['closed', 'done', 'resolved']
        completion_bonus = (estimated_hours * self.config['completion_bonus_percentage']) if is_completed else 0
        
        # Calculate fair efficiency score with bonuses
        numerator = productive_hours + completion_bonus + delivery_metrics['timing_bonus_hours']
        denominator = estimated_hours + delivery_metrics['late_penalty_mitigation']
        
        if denominator > 0:
            fair_efficiency = (numerator / denominator) * 100
            fair_efficiency = min(fair_efficiency, self.config['max_efficiency_cap'])
        else:
            fair_efficiency = 0
        
        # Traditional efficiency for comparison (productive time vs total time excluding paused)
        traditional_efficiency = (productive_hours / (total_hours - paused_hours)) * 100 if (total_hours - paused_hours) > 0 else 0
        
        return {
            "active_time_hours": round(productive_hours, 2),
            "paused_time_hours": round(paused_hours, 2),
            "total_time_hours": round(total_hours, 2),
            "estimated_time_hours": round(estimated_hours, 2),
            "efficiency_percentage": round(traditional_efficiency, 2),
            "fair_efficiency_score": round(fair_efficiency, 2),
            "delivery_score": round(delivery_metrics['delivery_score'], 2),
            "completion_bonus": round(completion_bonus, 2),
            "delivery_timing_bonus": round(delivery_metrics['timing_bonus_hours'], 2),
            "days_ahead_behind": delivery_metrics['days_difference'],
            "state_breakdown": state_durations,
            "paused_state_breakdown": state_stack.paused_time_accumulator,
            "was_reopened": pattern_summary.get('was_reopened', False),
            "active_after_reopen": round(pattern_summary.get('active_after_reopen_hours', 0), 2),
            "is_completed": pattern_summary.get('is_completed', False),
            "should_ignore": pattern_summary.get('should_ignore', False),
            "stack_summary": pattern_summary
        }
    
    
    def _calculate_estimated_time_from_work_item(self, work_item: Dict) -> float:
        """
        Calculate estimated time using OriginalEstimate field from Azure DevOps work item.
        Falls back to date-based calculation if OriginalEstimate is not available.
        """
        # Primary: Use OriginalEstimate field from work item
        original_estimate = work_item.get('original_estimate')
        if original_estimate and original_estimate > 0:
            return float(original_estimate)
        
        # Secondary: Calculate from start and target dates with office hours consideration
        start_date = work_item.get('start_date')
        target_date = work_item.get('target_date')
        
        if start_date and target_date:
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                target = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
                
                # Use office hours calculation for more accurate estimation
                office_hours = self._calculate_business_hours_between_dates(start, target)
                
                # Minimum 2 hours for any work item
                return max(office_hours, 2.0)
                
            except (ValueError, TypeError):
                pass
        
        # Fallback: use work item type to estimate
        work_item_type = work_item.get('work_item_type', '').lower()
        return self.config['default_work_item_hours'].get(work_item_type, 
                                                         self.config['default_work_item_hours']['default'])
    
    def _calculate_business_hours_between_dates(self, start_date: datetime, end_date: datetime) -> float:
        """
        Calculate business hours between start and target dates considering office hours.
        """
        if start_date >= end_date:
            return 0.0
        
        total_hours = 0.0
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            # Skip weekends
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
            
            # Calculate hours for this day
            if current_date == start_date.date() and current_date == end_date.date():
                # Same day - use actual start and end times within office hours
                day_start = max(start_date.time(), datetime.strptime('09:00', '%H:%M').time())
                day_end = min(end_date.time(), datetime.strptime('17:00', '%H:%M').time())
                if day_start < day_end:
                    day_hours = (datetime.combine(current_date, day_end) - 
                               datetime.combine(current_date, day_start)).total_seconds() / 3600
                    total_hours += min(day_hours, self.config['max_hours_per_day'])
            elif current_date == start_date.date():
                # First day - from start time to end of office hours
                day_start = max(start_date.time(), datetime.strptime('09:00', '%H:%M').time())
                day_end = datetime.strptime('17:00', '%H:%M').time()
                if day_start < day_end:
                    day_hours = (datetime.combine(current_date, day_end) - 
                               datetime.combine(current_date, day_start)).total_seconds() / 3600
                    total_hours += min(day_hours, self.config['max_hours_per_day'])
            elif current_date == end_date.date():
                # Last day - from start of office hours to end time
                day_start = datetime.strptime('09:00', '%H:%M').time()
                day_end = min(end_date.time(), datetime.strptime('17:00', '%H:%M').time())
                if day_start < day_end:
                    day_hours = (datetime.combine(current_date, day_end) - 
                               datetime.combine(current_date, day_start)).total_seconds() / 3600
                    total_hours += min(day_hours, self.config['max_hours_per_day'])
            else:
                # Full office day - 8 hours max
                total_hours += self.config['max_hours_per_day']
            
            current_date += timedelta(days=1)
        
        return round(total_hours, 2)
    
    def _calculate_delivery_timing(self, work_item: Dict) -> Dict:
        """Calculate delivery timing metrics and bonuses/penalties."""
        target_date = work_item.get('target_date')
        closed_date = work_item.get('closed_date')
        
        if not target_date or not closed_date:
            return {
                'delivery_score': 100.0,
                'timing_bonus_hours': 0.0,
                'late_penalty_mitigation': 0.0,
                'days_difference': 0
            }
        
        try:
            target = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
            closed = datetime.fromisoformat(closed_date.replace('Z', '+00:00'))
            
            days_difference = (closed - target).total_seconds() / 86400
            
            if days_difference <= 0:
                # Early or on-time delivery
                return self._calculate_early_delivery_bonus(days_difference)
            else:
                # Late delivery with graduated penalties
                return self._calculate_late_delivery_penalty(days_difference)
                
        except (ValueError, TypeError):
            return {
                'delivery_score': 100.0,
                'timing_bonus_hours': 0.0,
                'late_penalty_mitigation': 0.0,
                'days_difference': 0
            }
    
    def _calculate_early_delivery_bonus(self, days_difference: float) -> Dict:
        """Calculate bonus for early delivery."""
        thresholds = self.config['early_delivery_thresholds']
        scores = self.config['early_delivery_scores']
        bonuses = self.config['early_delivery_bonuses']
        
        if days_difference <= -thresholds['very_early_days']:
            delivery_score = scores['very_early']
            timing_bonus_hours = abs(days_difference) * bonuses['very_early']
        elif days_difference <= -thresholds['early_days']:
            delivery_score = scores['early']
            timing_bonus_hours = abs(days_difference) * bonuses['early']
        elif days_difference <= -thresholds['slightly_early_days']:
            delivery_score = scores['slightly_early']
            timing_bonus_hours = abs(days_difference) * bonuses['slightly_early']
        else:
            delivery_score = scores['on_time']
            timing_bonus_hours = 0.0
        
        return {
            'delivery_score': delivery_score,
            'timing_bonus_hours': timing_bonus_hours,
            'late_penalty_mitigation': 0.0,
            'days_difference': round(days_difference, 1)
        }
    
    def _calculate_late_delivery_penalty(self, days_difference: float) -> Dict:
        """Calculate penalty for late delivery."""
        scores = self.config['late_delivery_scores']
        mitigation = self.config['late_penalty_mitigation']
        
        if days_difference <= 3:
            delivery_score = scores['late_1_3']
            late_penalty_mitigation = mitigation['late_1_3']
        elif days_difference <= 7:
            delivery_score = scores['late_4_7']
            late_penalty_mitigation = mitigation['late_4_7']
        elif days_difference <= 14:
            delivery_score = scores['late_8_14']
            late_penalty_mitigation = mitigation['late_8_14']
        else:
            delivery_score = scores['late_15_plus']
            late_penalty_mitigation = mitigation['late_15_plus']
        
        return {
            'delivery_score': delivery_score,
            'timing_bonus_hours': 0.0,
            'late_penalty_mitigation': late_penalty_mitigation,
            'days_difference': round(days_difference, 1)
        }
    
    
    def calculate_developer_score(self, completion_rate: float, avg_fair_efficiency: float, 
                                avg_delivery_score: float, on_time_delivery: float) -> float:
        """Calculate overall developer score using configurable weights."""
        weights = self.config['developer_score_weights']
        
        overall_score = (
            (avg_fair_efficiency * weights['fair_efficiency']) +
            (avg_delivery_score * weights['delivery_score']) +
            (completion_rate * weights['completion_rate']) +
            (min(100, on_time_delivery) * weights['on_time_delivery'])
        )
        
        return round(overall_score, 2)
    
    def _empty_efficiency_metrics(self) -> Dict:
        """Return empty efficiency metrics structure."""
        return {
            "active_time_hours": 0,
            "paused_time_hours": 0,
            "total_time_hours": 0,
            "estimated_time_hours": 0,
            "efficiency_percentage": 0,
            "fair_efficiency_score": 0,
            "delivery_score": 0,
            "completion_bonus": 0,
            "delivery_timing_bonus": 0,
            "days_ahead_behind": 0,
            "state_breakdown": {},
            "paused_state_breakdown": {},
            "was_reopened": False,
            "active_after_reopen": 0,
            "is_completed": False,
            "should_ignore": False,
            "stack_summary": {}
        }
    
    def _ignored_work_item_metrics(self) -> Dict:
        """Return metrics structure for ignored work items."""
        return {
            "active_time_hours": 0,
            "paused_time_hours": 0,
            "total_time_hours": 0,
            "estimated_time_hours": 0,
            "efficiency_percentage": 0,
            "fair_efficiency_score": 0,
            "delivery_score": 0,
            "completion_bonus": 0,
            "delivery_timing_bonus": 0,
            "days_ahead_behind": 0,
            "state_breakdown": {},
            "paused_state_breakdown": {},
            "was_reopened": False,
            "active_after_reopen": 0,
            "is_completed": False,
            "should_ignore": True,
            "stack_summary": {"should_ignore": True}
        }