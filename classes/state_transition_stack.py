"""
Stack-based state transition tracking for Azure DevOps work items.
Efficiently tracks state changes and calculates time metrics with business hours logic.
"""

from datetime import datetime, timedelta, time
from typing import List, Dict, Optional, Tuple
import pytz


class StateTransition:
    """Represents a single state transition with context."""
    
    def __init__(self, state: str, timestamp: datetime, reason: str = "", 
                 changed_by: str = "", revision: int = 0):
        self.state = state
        self.timestamp = timestamp
        self.reason = reason
        self.changed_by = changed_by
        self.revision = revision
        self.time_in_state = timedelta()
    
    def __repr__(self):
        return f"StateTransition(state='{self.state}', timestamp={self.timestamp}, reason='{self.reason}')"


class WorkItemStateStack:
    """Stack-based tracking of work item state transitions with business hours calculation and state categories."""
    
    def __init__(self, office_start_hour: int = 9, office_end_hour: int = 17, 
                 max_hours_per_day: int = 8, timezone_str: str = "America/Mexico_City",
                 state_config: Optional[Dict] = None,
                 timeframe_start: Optional[str] = None, timeframe_end: Optional[str] = None):
        """
        Initialize state stack with office hours configuration and state categories.
        
        Args:
            office_start_hour: Start of office hours (24-hour format)
            office_end_hour: End of office hours (24-hour format)
            max_hours_per_day: Maximum productive hours to count per day
            timezone_str: Timezone for office hours calculation
            state_config: Configuration for state categories and behaviors
            timeframe_start: Start date of the query timeframe (YYYY-MM-DD format)
            timeframe_end: End date of the query timeframe (YYYY-MM-DD format)
        """
        self.transitions = []  # Stack of state transitions
        self.time_accumulator = {}  # Running totals per state (business hours)
        self.paused_time_accumulator = {}  # Time spent in pause/stopper states
        self.current_state = None
        self.entry_time = None
        self.is_currently_paused = False
        self.pause_start_time = None
        
        # Office hours configuration
        self.office_start = time(office_start_hour, 0)
        self.office_end = time(office_end_hour, 0)
        self.max_hours_per_day = max_hours_per_day
        self.timezone = pytz.timezone(timezone_str)
        
        # State configuration
        self.state_config = state_config or {}
        self.productive_states = self.state_config.get('productive_states', [])
        self.pause_stopper_states = self.state_config.get('pause_stopper_states', [])
        self.completion_states = self.state_config.get('completion_states', [])
        self.ignored_states = self.state_config.get('ignored_states', [])
        
        # Metrics
        self.total_productive_hours = 0
        self.total_paused_hours = 0
        self.total_calendar_time = timedelta()
        self.was_reopened = False
        self.active_after_reopen_hours = 0
        self.is_completed = False
        self.should_ignore = False
        
        # Timeframe filtering
        self.timeframe_start_dt = None
        self.timeframe_end_dt = None
        if timeframe_start:
            try:
                self.timeframe_start_dt = datetime.fromisoformat(f"{timeframe_start}T00:00:00+00:00")
            except (ValueError, TypeError):
                pass
        if timeframe_end:
            try:
                self.timeframe_end_dt = datetime.fromisoformat(f"{timeframe_end}T23:59:59+00:00")
            except (ValueError, TypeError):
                pass
    
    def push_state(self, new_state: str, timestamp: datetime, reason: str = "", 
                   changed_by: str = "", revision: int = 0):
        """
        Push a new state transition onto the stack with state category handling.
        
        Args:
            new_state: The new state
            timestamp: When the transition occurred
            reason: Reason for the transition
            changed_by: Who made the change
            revision: Revision number
        """
        # Check if we should ignore this work item
        if new_state in self.ignored_states:
            self.should_ignore = True
            return
        
        # Check if work item is completed
        if new_state in self.completion_states:
            self.is_completed = True
        
        # Ensure timestamp is timezone-aware
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=pytz.UTC)
        
        # If we have a current state, calculate time spent in it
        if self.current_state and self.entry_time:
            # Calculate time in current state
            time_in_state = self._calculate_time_in_state(
                self.entry_time, timestamp, self.current_state
            )
            
            # Update appropriate accumulator based on state type
            if self.current_state in self.productive_states:
                # Productive state - count toward efficiency
                if self.current_state not in self.time_accumulator:
                    self.time_accumulator[self.current_state] = 0
                self.time_accumulator[self.current_state] += time_in_state
                self.total_productive_hours += time_in_state
                
                # Track active time after reopen for bonus calculation
                if self.was_reopened:
                    self.active_after_reopen_hours += time_in_state
                    
            elif self.current_state in self.pause_stopper_states:
                # Pause/stopper state - track separately, don't count toward efficiency
                if self.current_state not in self.paused_time_accumulator:
                    self.paused_time_accumulator[self.current_state] = 0
                self.paused_time_accumulator[self.current_state] += time_in_state
                self.total_paused_hours += time_in_state
            else:
                # Other states (assigned, completion, etc.) - track but don't count toward efficiency
                if self.current_state not in self.time_accumulator:
                    self.time_accumulator[self.current_state] = 0
                self.time_accumulator[self.current_state] += time_in_state
            
            # Update the transition object
            if self.transitions:
                self.transitions[-1].time_in_state = timedelta(hours=time_in_state)
            
            # Calculate total calendar time
            calendar_time = timestamp - self.entry_time
            self.total_calendar_time += calendar_time
            
            # Check for reopened pattern (completion -> productive)
            if (self.current_state in self.completion_states and 
                new_state in self.productive_states):
                self.was_reopened = True
        
        # Create new transition
        transition = StateTransition(new_state, timestamp, reason, changed_by, revision)
        self.transitions.append(transition)
        
        # Update current state
        self.current_state = new_state
        self.entry_time = timestamp
    
    def _calculate_time_in_state(self, start_time: datetime, end_time: datetime, 
                               state: str) -> float:
        """
        Calculate time spent in a specific state, applying business hours logic for productive states.
        Only counts time that falls within the specified timeframe for productive states.
        
        Args:
            start_time: Start datetime (timezone-aware)
            end_time: End datetime (timezone-aware) 
            state: The state name
            
        Returns:
            Total hours as float
        """
        # For productive states, apply timeframe filtering and use business hours calculation
        if state in self.productive_states:
            # Apply timeframe filtering for productive states only
            filtered_start, filtered_end = self._apply_timeframe_filtering(start_time, end_time)
            if filtered_start >= filtered_end:
                return 0.0  # No time within timeframe
            return self._calculate_business_hours_in_period(filtered_start, filtered_end)
        else:
            # For non-productive states, use calendar time but still respect weekends/office hours
            # No timeframe filtering for non-productive states
            return self._calculate_business_hours_in_period(start_time, end_time, count_all_hours=True)
    
    def _apply_timeframe_filtering(self, start_time: datetime, end_time: datetime) -> Tuple[datetime, datetime]:
        """
        Filter the time period to only include the portion that falls within the specified timeframe.
        
        Args:
            start_time: Original start time
            end_time: Original end time
            
        Returns:
            Tuple of (filtered_start, filtered_end) datetime objects
        """
        filtered_start = start_time
        filtered_end = end_time
        
        # Apply timeframe start filter
        if self.timeframe_start_dt and start_time < self.timeframe_start_dt:
            filtered_start = self.timeframe_start_dt
            
        # Apply timeframe end filter  
        if self.timeframe_end_dt and end_time > self.timeframe_end_dt:
            filtered_end = self.timeframe_end_dt
            
        return filtered_start, filtered_end
    
    def _calculate_business_hours_in_period(self, start_time: datetime, end_time: datetime, 
                                          count_all_hours: bool = False) -> float:
        """
        Calculate business hours between two timestamps with office hours consideration.
        
        Args:
            start_time: Start datetime (timezone-aware)
            end_time: End datetime (timezone-aware)
            count_all_hours: If True, count all hours within office hours, otherwise apply daily cap
            
        Returns:
            Total business hours as float
        """
        if start_time >= end_time:
            return 0.0
        
        # Convert to local timezone for office hours calculation
        local_start = start_time.astimezone(self.timezone)
        local_end = end_time.astimezone(self.timezone)
        
        total_hours = 0.0
        current_date = local_start.date()
        end_date = local_end.date()
        
        while current_date <= end_date:
            # Skip weekends (Monday=0, Sunday=6)
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                continue
            
            # Calculate daily hours based on office hours and date boundaries
            day_start, day_end = self._get_day_boundaries(current_date, local_start, local_end)
            
            if day_start and day_end and day_start < day_end:
                # Calculate hours within office hours
                office_hours = self._calculate_office_hours_in_day(day_start, day_end)
                
                # Apply daily cap only for productive states unless counting all hours
                if count_all_hours:
                    daily_hours = office_hours
                else:
                    daily_hours = min(office_hours, self.max_hours_per_day)
                
                total_hours += daily_hours
            
            current_date += timedelta(days=1)
        
        return round(total_hours, 2)
    
    def _get_day_boundaries(self, current_date: datetime.date, 
                           period_start: datetime, period_end: datetime) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Get the effective start and end times for a specific day within the period."""
        
        # Create datetime objects for the full day in local timezone
        day_start = datetime.combine(current_date, datetime.min.time()).replace(tzinfo=self.timezone)
        day_end = datetime.combine(current_date, datetime.max.time()).replace(tzinfo=self.timezone)
        
        # Constrain to the actual period
        if current_date == period_start.date():
            day_start = period_start
        if current_date == period_end.date():
            day_end = period_end
        
        # If the day doesn't overlap with our period, return None
        if day_start >= day_end:
            return None, None
            
        return day_start, day_end
    
    def _calculate_office_hours_in_day(self, day_start: datetime, day_end: datetime) -> float:
        """Calculate office hours within a single day period."""
        
        # Create office hour boundaries for this day
        office_start_dt = datetime.combine(day_start.date(), self.office_start).replace(tzinfo=self.timezone)
        office_end_dt = datetime.combine(day_start.date(), self.office_end).replace(tzinfo=self.timezone)
        
        # Find the intersection of the period with office hours
        effective_start = max(day_start, office_start_dt)
        effective_end = min(day_end, office_end_dt)
        
        # If there's no overlap with office hours, return 0
        if effective_start >= effective_end:
            return 0.0
        
        # Calculate the overlap in hours
        overlap = effective_end - effective_start
        return overlap.total_seconds() / 3600
    
    def get_state_durations(self) -> Dict[str, float]:
        """Get total time spent in each state (business hours)."""
        return self.time_accumulator.copy()
    
    def get_total_productive_hours(self) -> float:
        """Get total productive business hours."""
        return self.total_productive_hours
    
    def get_total_paused_hours(self) -> float:
        """Get total paused/stopper hours."""
        return self.total_paused_hours
    
    def get_total_time_all_states(self) -> float:
        """Get total time across all states."""
        total = sum(self.time_accumulator.values()) + sum(self.paused_time_accumulator.values())
        return total
    
    def should_ignore_work_item(self) -> bool:
        """Check if this work item should be ignored from analysis."""
        return self.should_ignore
    
    def get_pattern_summary(self) -> Dict:
        """Get summary of state transition patterns."""
        if not self.transitions:
            return {}
        
        return {
            'total_transitions': len(self.transitions),
            'states_visited': list(set(t.state for t in self.transitions)),
            'was_reopened': self.was_reopened,
            'active_after_reopen_hours': self.active_after_reopen_hours,
            'total_productive_hours': self.total_productive_hours,
            'total_paused_hours': self.total_paused_hours,
            'total_calendar_days': self.total_calendar_time.days,
            'is_completed': self.is_completed,
            'should_ignore': self.should_ignore,
            'productive_states_used': [s for s in self.time_accumulator.keys() if s in self.productive_states],
            'pause_states_used': list(self.paused_time_accumulator.keys())
        }
    
    def detect_bottlenecks(self, threshold_hours: float = 16) -> List[Dict]:
        """Detect states where work items spent too much time."""
        bottlenecks = []
        
        for state, hours in self.time_accumulator.items():
            if hours > threshold_hours:
                # Find the transition for context
                transition = next((t for t in self.transitions if t.state == state), None)
                bottlenecks.append({
                    'state': state,
                    'hours_spent': hours,
                    'reason': transition.reason if transition else "Unknown",
                    'changed_by': transition.changed_by if transition else "Unknown"
                })
        
        return sorted(bottlenecks, key=lambda x: x['hours_spent'], reverse=True)
    
    @classmethod
    def from_revision_history(cls, revision_history: List[Dict], 
                             office_start_hour: int = 9, office_end_hour: int = 17,
                             max_hours_per_day: int = 8, timezone_str: str = "America/Mexico_City",
                             state_config: Optional[Dict] = None,
                             timeframe_start: Optional[str] = None, timeframe_end: Optional[str] = None) -> 'WorkItemStateStack':
        """
        Create a state stack from Azure DevOps revision history.
        
        Args:
            revision_history: List of revision dictionaries from Azure DevOps API
            office_start_hour: Start of office hours
            office_end_hour: End of office hours  
            max_hours_per_day: Maximum hours to count per day
            timezone_str: Timezone for calculations
            state_config: Configuration for state categories
            timeframe_start: Start date of the query timeframe (YYYY-MM-DD format)
            timeframe_end: End date of the query timeframe (YYYY-MM-DD format)
            
        Returns:
            Populated WorkItemStateStack
        """
        stack = cls(office_start_hour, office_end_hour, max_hours_per_day, timezone_str, state_config, timeframe_start, timeframe_end)
        
        # Sort revisions by revision number to ensure chronological order
        sorted_revisions = sorted(revision_history, key=lambda x: x.get('revision', 0))
        
        for revision in sorted_revisions:
            timestamp_str = revision.get('changed_date', '')
            if timestamp_str:
                # Handle different timestamp formats
                timestamp = cls._parse_timestamp(timestamp_str)
                
                stack.push_state(
                    new_state=revision.get('state', ''),
                    timestamp=timestamp,
                    reason=revision.get('reason', ''),
                    changed_by=revision.get('changed_by', ''),
                    revision=revision.get('revision', 0)
                )
        
        return stack
    
    @staticmethod
    def _parse_timestamp(timestamp_str: str) -> datetime:
        """Parse timestamp string from Azure DevOps API."""
        # Remove 'Z' suffix and handle timezone
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1] + '+00:00'
        
        try:
            return datetime.fromisoformat(timestamp_str)
        except ValueError:
            # Fallback for other formats
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))


def create_stack_from_work_item(work_item_data: Dict, revision_history: List[Dict],
                               state_config: Optional[Dict] = None,
                               office_hours_config: Optional[Dict] = None,
                               timeframe_start: Optional[str] = None,
                               timeframe_end: Optional[str] = None) -> WorkItemStateStack:
    """
    Create a complete state stack from work item data and revision history.
    
    Args:
        work_item_data: Work item fields data
        revision_history: List of state change revisions
        state_config: Configuration for state categories and behaviors
        office_hours_config: Office hours configuration
        timeframe_start: Start date of the query timeframe (YYYY-MM-DD format)
        timeframe_end: End date of the query timeframe (YYYY-MM-DD format)
        
    Returns:
        Configured WorkItemStateStack with calculated metrics
    """
    # Default office hours configuration
    if office_hours_config is None:
        office_hours_config = {
            'office_start_hour': 9,
            'office_end_hour': 17,
            'max_hours_per_day': 8,
            'timezone_str': 'America/Mexico_City'
        }
    
    # Create stack from revision history
    stack = WorkItemStateStack.from_revision_history(
        revision_history,
        state_config=state_config,
        timeframe_start=timeframe_start,
        timeframe_end=timeframe_end,
        **office_hours_config
    )
    
    return stack