from typing import List, Dict
from app.schemas.event import Event
from app.state import state
import logging

logger = logging.getLogger(__name__)


class EventReadService:
	"""Service for Event read operations."""

	@staticmethod
	def get_event(event_key: str) -> Event:
		"""
		Get an event by key.
		
		Args:
			event_key: Key of event to retrieve
		
		Returns:
			Event object
		
		Raises:
			NotFoundError: If event is not found
		"""
		event = state.get_event(event_key)
		if event is None:
			from app.exceptions import NotFoundError
			raise NotFoundError("Event", event_key)
		return event
	
	@staticmethod
	def has_episode(event_key: str) -> bool:
		"""
		Check if an event has an associated episode.
		
		Args:
			event_key: Key of event to check
		
		Returns:
			True if event has an episode_key, False otherwise
		"""
		try:
			event = EventReadService.get_event(event_key)
			return event.episode_key is not None
		except Exception:
			return False
	
	@staticmethod
	def get_events(active_only: bool = True) -> List[Event]:
		"""
		Get events from state, optionally filtered by active_only.
		
		Filtering logic:
		- If active_only is True, return only events from state.active_events
		- Otherwise, return all events from state.events
		
		Args:
			active_only: If true, return only events from state.active_events. Default is True.
		
		Returns:
			List of Event objects matching the filter criteria
		"""
		# If active_only is True, use active_events; otherwise use all events
		return state.active_events if active_only else state.events
	
	@staticmethod
	def get_active_event_counts_by_type() -> Dict[str, int]:
		"""
		Get count of active events grouped by event type.
		
		Returns:
			Dictionary mapping event_type to count of active events
		"""
		active_events = state.active_events
		counts: Dict[str, int] = {}
		
		for event in active_events:
			event_type = event.event_type
			counts[event_type] = counts.get(event_type, 0) + 1
		
		return counts
