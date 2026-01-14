"""
Unit tests for EventReadService.
"""
import pytest
from unittest.mock import Mock, patch, PropertyMock
from datetime import datetime, timezone, timedelta
from app.services.event_read_service import EventReadService
from app.schemas.event import Event

class TestGetEvents:
	"""Test cases for EventReadService.get_events filtering functionality."""
	
	@patch('app.services.event_read_service.state')
	def test_get_events_returns_active_events_by_default(self, mock_state):
		"""Test get_events returns only active events by default (active_only=True)."""
		active_event = Event(
			event_key="event-1",
			nws_alert_id="alert-1",
			event_type="TOR",
			start_date=datetime.now(timezone.utc),
			description="Active event",
			is_active=True,
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/"
		)
		
		inactive_event = Event(
			event_key="event-2",
			nws_alert_id="alert-2",
			event_type="TOR",
			start_date=datetime.now(timezone.utc),
			description="Inactive event",
			is_active=False,
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/"
		)
		
		mock_state.events = [active_event, inactive_event]
		mock_state.active_events = [active_event]
		
		result = EventReadService.get_events()
		
		# Should return only active events by default
		assert len(result) == 1
		assert result[0].event_key == "event-1"
	
	@patch('app.services.event_read_service.state')
	def test_get_events_with_active_only_true_returns_only_active_events(self, mock_state):
		"""Test get_events with active_only=True returns only active events."""
		active_event_1 = Event(
			event_key="active-1",
			nws_alert_id="alert-1",
			event_type="TOR",
			start_date=datetime.now(timezone.utc),
			description="Active event 1",
			is_active=True,
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/"
		)
		
		active_event_2 = Event(
			event_key="active-2",
			nws_alert_id="alert-2",
			event_type="TOR",
			start_date=datetime.now(timezone.utc),
			description="Active event 2",
			is_active=True,
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/"
		)
		
		inactive_event = Event(
			event_key="inactive-1",
			nws_alert_id="alert-3",
			event_type="TOR",
			start_date=datetime.now(timezone.utc),
			description="Inactive event",
			is_active=False,
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/"
		)
		
		mock_state.events = [active_event_1, inactive_event, active_event_2]
		mock_state.active_events = [active_event_1, active_event_2]
		
		result = EventReadService.get_events(active_only=True)
		
		# Should return only active events
		assert len(result) == 2
		event_keys = {event.event_key for event in result}
		assert "active-1" in event_keys
		assert "active-2" in event_keys
		assert "inactive-1" not in event_keys
	
	@patch('app.services.event_read_service.state')
	def test_get_events_with_active_only_false_returns_all_events(self, mock_state):
		"""Test get_events with active_only=False returns all events."""
		active_event = Event(
			event_key="active-1",
			nws_alert_id="alert-1",
			event_type="TOR",
			start_date=datetime.now(timezone.utc),
			description="Active event",
			is_active=True,
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/"
		)
		
		inactive_event = Event(
			event_key="inactive-1",
			nws_alert_id="alert-2",
			event_type="TOR",
			start_date=datetime.now(timezone.utc),
			description="Inactive event",
			is_active=False,
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/"
		)
		
		mock_state.events = [active_event, inactive_event]
		
		result = EventReadService.get_events(active_only=False)
		
		# Should return all events
		assert len(result) == 2
		event_keys = {event.event_key for event in result}
		assert "active-1" in event_keys
		assert "inactive-1" in event_keys
	
	@patch('app.services.event_read_service.state')
	def test_get_events_with_active_only_returns_empty_when_no_active_events(self, mock_state):
		"""Test get_events with active_only=True returns empty list when no active events."""
		inactive_event_1 = Event(
			event_key="inactive-1",
			nws_alert_id="alert-1",
			event_type="TOR",
			start_date=datetime.now(timezone.utc),
			description="Inactive event 1",
			is_active=False,
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/"
		)
		
		inactive_event_2 = Event(
			event_key="inactive-2",
			nws_alert_id="alert-2",
			event_type="TOR",
			start_date=datetime.now(timezone.utc),
			description="Inactive event 2",
			is_active=False,
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/"
		)
		
		mock_state.events = [inactive_event_1, inactive_event_2]
		mock_state.active_events = []
		
		result = EventReadService.get_events(active_only=True)
		
		# Should return empty list
		assert len(result) == 0




class TestStateActiveEvents:
	"""Test cases for State.active_events property."""
	
	@patch('app.state.quantagent_redis')
	def test_active_events_filters_by_is_active(self, mock_redis):
		"""Test that active_events only returns events where is_active=True."""
		from app.state import State
		
		# Create mock events
		active_event = Event(
			event_key="active-event",
			nws_alert_id="alert-1",
			event_type="TOR",
			start_date=datetime.now(timezone.utc),
			description="Active",
			is_active=True,
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/"
		)
		
		inactive_event = Event(
			event_key="inactive-event",
			nws_alert_id="alert-2",
			event_type="TOR",
			start_date=datetime.now(timezone.utc),
			description="Inactive",
			is_active=False,
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/"
		)
		
		# Mock Redis to return both events using read_all_as_schema
		mock_redis.get_all_keys.return_value = ["event:active-event", "event:inactive-event"]
		mock_redis.read_all_as_schema.return_value = [active_event, inactive_event]
		
		state = State()
		result = state.active_events
		
		# Should only return active event
		assert len(result) == 1
		assert result[0].event_key == "active-event"
		assert result[0].is_active is True
	
	@patch('app.state.quantagent_redis')
	def test_active_events_returns_empty_list_when_no_active_events(self, mock_redis):
		"""Test that active_events returns empty list when no active events exist."""
		from app.state import State
		
		inactive_event = Event(
			event_key="inactive-event",
			nws_alert_id="alert-1",
			event_type="TOR",
			start_date=datetime.now(timezone.utc),
			description="Inactive",
			is_active=False,
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/"
		)
		
		mock_redis.get_all_keys.return_value = ["event:inactive-event"]
		mock_redis.read_all_as_schema.return_value = [inactive_event]
		
		state = State()
		result = state.active_events
		
		assert len(result) == 0
	
	@patch('app.state.quantagent_redis')
	def test_active_events_handles_mixed_active_inactive(self, mock_redis):
		"""Test that active_events correctly filters mixed active/inactive events."""
		from app.state import State
		
		active_event_1 = Event(
			event_key="active-1",
			nws_alert_id="alert-1",
			event_type="TOR",
			start_date=datetime.now(timezone.utc),
			description="Active 1",
			is_active=True,
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/"
		)
		
		active_event_2 = Event(
			event_key="active-2",
			nws_alert_id="alert-2",
			event_type="TOR",
			start_date=datetime.now(timezone.utc),
			description="Active 2",
			is_active=True,
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/"
		)
		
		inactive_event = Event(
			event_key="inactive",
			nws_alert_id="alert-3",
			event_type="TOR",
			start_date=datetime.now(timezone.utc),
			description="Inactive",
			is_active=False,
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/"
		)
		
		mock_redis.get_all_keys.return_value = ["event:active-1", "event:inactive", "event:active-2"]
		mock_redis.read_all_as_schema.return_value = [active_event_1, inactive_event, active_event_2]
		
		state = State()
		result = state.active_events
		
		# Should return only the 2 active events
		assert len(result) == 2
		event_keys = {event.event_key for event in result}
		assert "active-1" in event_keys
		assert "active-2" in event_keys
		assert "inactive" not in event_keys
