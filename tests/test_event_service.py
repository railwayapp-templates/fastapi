"""
Comprehensive unit tests for EventService methods.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, PropertyMock
from datetime import datetime, timezone, timedelta
from app.services.event_service import EventService
from app.services.event_completion_service import EventCompletionService
from app.shared_models.nws_poller_models import FilteredNWSAlert
from app.schemas.event import Event
from app.schemas.location import Location, Coordinate
from app.exceptions import NotFoundError
from app.exceptions.base import ConflictError
from app.utils.event_types import NWS_WARNING_CODES


class TestCreateEventFromAlert:
	"""Test cases for EventService.create_event_from_alert."""
	
	@pytest.fixture
	def sample_alert(self):
		"""Create a sample FilteredNWSAlert for testing."""
		return FilteredNWSAlert(
			alert_id="https://api.weather.gov/alerts/urn:oid:2.49.0.1.840.0.1234567890",
			key="KFWD.TO.W.0015.2024",
			event_type="TOR",
			message_type="NEW",
			is_watch=False,
			is_warning=True,
			severity="Extreme",
			urgency="Immediate",
			certainty="Observed",
			effective="2024-01-15T10:00:00-06:00",
			expires="2024-01-15T11:00:00-06:00",
			expected_end="2024-01-15T11:00:00-06:00",
			headline="Tornado Warning",
			description="Test tornado warning description",
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/",
			affected_zones_ugc_endpoints=["https://api.weather.gov/zones/forecast/TXC113"],
			affected_zones_raw_ugc_codes=["TXC113"],
			referenced_alerts=[],
			locations=[
				Location(
					episode_key=None,
					event_key="KFWD.TO.W.0015.2024",
					state_fips="48",
					county_fips="113",
					ugc_code="TXC113",
					shape=[Coordinate(latitude=32.8, longitude=-97.5)],
					full_zone_ugc_endpoint="https://api.weather.gov/zones/forecast/TXC113"
				)
			]
		)
	
	@patch('app.services.event_create_service.state')
	def test_create_event_from_alert_success(self, mock_state, sample_alert):
		"""Test successful event creation from alert."""
		# Setup
		mock_state.event_exists.return_value = False
		mock_state.add_event = Mock()
		
		# Execute
		result = EventService.create_event_from_alert(sample_alert)
		
		# Assertions
		assert isinstance(result, Event)
		assert result.event_key == sample_alert.key
		assert result.nws_alert_id == sample_alert.alert_id
		assert result.event_type == sample_alert.event_type
		assert result.hr_event_type == NWS_WARNING_CODES.get("TOR", "UNKNOWN")
		assert result.episode_key is None
		assert result.is_active is True
		assert result.locations == sample_alert.locations
		assert result.raw_vtec == sample_alert.raw_vtec
		assert result.previous_ids == []
		assert "Tornado Warning" in result.description
		assert "Test tornado warning description" in result.description
		assert result.updated_at is not None
		mock_state.add_event.assert_called_once_with(result)
	
	@patch('app.services.event_create_service.state')
	def test_create_event_from_alert_with_missing_dates(self, mock_state):
		"""Test event creation when optional dates are missing."""
		# Setup
		mock_state.event_exists.return_value = False
		mock_state.add_event = Mock()
		
		# Note: effective is required, but expected_end is optional
		alert = FilteredNWSAlert(
			alert_id="test-alert-1",
			key="KFWD.TO.W.0015.2024",
			event_type="TOR",
			message_type="NEW",
			is_watch=False,
			is_warning=True,
			severity="Extreme",
			urgency="Immediate",
			certainty="Observed",
			effective="2024-01-15T10:00:00-06:00",  # Required field
			expires=None,
			expected_end=None,  # Optional field
			headline=None,
			description=None,
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/",
			affected_zones_ugc_endpoints=[],
			affected_zones_raw_ugc_codes=[],
			referenced_alerts=[],
			locations=[]
		)
		
		# Execute
		result = EventService.create_event_from_alert(alert)
		
		# Assertions
		assert result.start_date is not None  # Should be parsed from effective
		assert result.expected_end_date is None  # Should be None when expected_end is None
		assert result.description == "\n\n"  # Empty headline and description
	
	@patch('app.services.event_create_service.state')
	def test_create_event_from_alert_conflict_error(self, mock_state, sample_alert):
		"""Test that ConflictError is raised when event already exists."""
		# Setup
		mock_state.event_exists.return_value = True
		
		# Execute & Assert
		with pytest.raises(ConflictError) as exc_info:
			EventService.create_event_from_alert(sample_alert)
		
		assert "already exists" in str(exc_info.value)
		assert sample_alert.key in str(exc_info.value)
	
	@patch('app.services.event_create_service.state')
	def test_create_event_from_alert_unknown_event_type(self, mock_state):
		"""Test event creation with unknown event type."""
		# Setup
		mock_state.event_exists.return_value = False
		mock_state.add_event = Mock()
		
		alert = FilteredNWSAlert(
			alert_id="test-alert-1",
			key="KFWD.XXX.W.0015.2024",
			event_type="XXX",
			message_type="NEW",
			is_watch=False,
			is_warning=True,
			severity="Extreme",
			urgency="Immediate",
			certainty="Observed",
			effective="2024-01-15T10:00:00-06:00",
			expires="2024-01-15T11:00:00-06:00",
			expected_end="2024-01-15T11:00:00-06:00",
			headline="Test",
			description="Test",
			raw_vtec="/O.NEW.KFWD.XXX.W.0015.240115T1000Z-240115T1100Z/",
			affected_zones_ugc_endpoints=[],
			affected_zones_raw_ugc_codes=[],
			referenced_alerts=[],
			locations=[]
		)
		
		# Execute
		result = EventService.create_event_from_alert(alert)
		
		# Assertions
		assert result.hr_event_type == "UNKNOWN"
	
	@patch('app.services.event_create_service.state')
	def test_create_event_from_alert_preserves_all_fields(self, mock_state, sample_alert):
		"""Test that all alert fields are properly mapped to event."""
		# Setup
		mock_state.event_exists.return_value = False
		mock_state.add_event = Mock()
		
		# Execute
		result = EventService.create_event_from_alert(sample_alert)
		
		# Assertions - verify all fields are set correctly
		assert result.event_key == "KFWD.TO.W.0015.2024"
		assert result.nws_alert_id == "https://api.weather.gov/alerts/urn:oid:2.49.0.1.840.0.1234567890"
		assert len(result.locations) == 1
		assert result.locations[0].ugc_code == "TXC113"
		assert result.is_active is True


class TestUpdateEventFromAlert:
	"""Test cases for EventService.update_event_from_alert."""
	
	@pytest.fixture
	def existing_event(self):
		"""Create an existing event for testing."""
		return Event(
			event_key="KFWD.TO.W.0015.2024",
			nws_alert_id="https://api.weather.gov/alerts/urn:oid:2.49.0.1.840.0.1234567890",
			episode_key="EP001",
			event_type="TOR",
			hr_event_type="Tornado Warning",
			locations=[
				Location(
					episode_key="EP001",
					event_key="KFWD.TO.W.0015.2024",
					state_fips="48",
					county_fips="113",
					ugc_code="TXC113",
					shape=[Coordinate(latitude=32.8, longitude=-97.5)],
					full_zone_ugc_endpoint="https://api.weather.gov/zones/forecast/TXC113"
				)
			],
			start_date=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
			expected_end_date=datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc),
			actual_end_date=None,
			updated_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
			description="Original description",
			is_active=True,
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/",
			previous_ids=[],
			property_damage=1000,
			crops_damage=500,
			range_miles=5.0
		)
	
	@pytest.fixture
	def update_alert(self):
		"""Create an update alert for testing."""
		return FilteredNWSAlert(
			alert_id="https://api.weather.gov/alerts/urn:oid:2.49.0.1.840.0.1234567891",
			key="KFWD.TO.W.0015.2024",
			event_type="TOR",
			message_type="CON",
			is_watch=False,
			is_warning=True,
			severity="Extreme",
			urgency="Immediate",
			certainty="Observed",
			effective="2024-01-15T10:30:00-06:00",
			expires="2024-01-15T12:00:00-06:00",
			expected_end="2024-01-15T12:00:00-06:00",
			headline="Updated Tornado Warning",
			description="Updated description",
			raw_vtec="/O.CON.KFWD.TO.W.0015.240115T1030Z-240115T1200Z/",
			affected_zones_ugc_endpoints=["https://api.weather.gov/zones/forecast/TXC113"],
			affected_zones_raw_ugc_codes=["TXC113"],
			referenced_alerts=[],
			locations=[
				Location(
					episode_key=None,
					event_key="KFWD.TO.W.0015.2024",
					state_fips="48",
					county_fips="113",
					ugc_code="TXC113",
					shape=[Coordinate(latitude=32.8, longitude=-97.5)],
					full_zone_ugc_endpoint="https://api.weather.gov/zones/forecast/TXC113"
				)
			]
		)
	
	@patch('app.services.event_read_service.EventReadService.get_event')
	@patch('app.services.event_update_service.state')
	def test_update_event_standard_update(self, mock_state, mock_get_event, existing_event, update_alert):
		"""Test standard update (CON message type) - merges locations and updates fields."""
		# Setup
		mock_get_event.return_value = existing_event
		mock_state.update_event = Mock()
		
		# Execute
		result = EventService.update_event_from_alert(update_alert)
		
		# Assertions
		assert isinstance(result, Event)
		assert result.event_key == existing_event.event_key
		assert result.nws_alert_id == update_alert.alert_id  # New alert ID
		assert result.episode_key == existing_event.episode_key  # Preserved
		assert result.event_type == existing_event.event_type  # Preserved
		assert result.start_date == existing_event.start_date  # Preserved
		assert result.expected_end_date is not None  # Updated
		assert result.actual_end_date == existing_event.actual_end_date  # Preserved
		assert "Updated Tornado Warning" in result.description
		assert "Updated description" in result.description
		assert result.raw_vtec == update_alert.raw_vtec  # Updated
		assert result.is_active == existing_event.is_active  # Preserved
		assert result.property_damage == existing_event.property_damage  # Preserved
		assert result.crops_damage == existing_event.crops_damage  # Preserved
		assert result.range_miles == existing_event.range_miles  # Preserved
		assert existing_event.nws_alert_id in result.previous_ids  # Old ID added
		mock_state.update_event.assert_called_once_with(result)
	
	@patch('app.services.event_read_service.EventReadService.get_event')
	@patch('app.services.event_update_service.state')
	def test_update_event_cor_message_type(self, mock_state, mock_get_event, existing_event):
		"""Test COR (Correction) message type - replaces entire event."""
		# Setup
		mock_get_event.return_value = existing_event
		mock_state.update_event = Mock()
		
		cor_alert = FilteredNWSAlert(
			alert_id="https://api.weather.gov/alerts/urn:oid:2.49.0.1.840.0.1234567892",
			key="KFWD.TO.W.0015.2024",
			event_type="TOR",
			message_type="COR",
			is_watch=False,
			is_warning=True,
			severity="Extreme",
			urgency="Immediate",
			certainty="Observed",
			effective="2024-01-15T10:30:00-06:00",
			expires="2024-01-15T12:00:00-06:00",
			expected_end="2024-01-15T12:00:00-06:00",
			headline="Corrected Tornado Warning",
			description="Corrected description",
			raw_vtec="/O.COR.KFWD.TO.W.0015.240115T1030Z-240115T1200Z/",
			affected_zones_ugc_endpoints=["https://api.weather.gov/zones/forecast/TXC113"],
			affected_zones_raw_ugc_codes=["TXC113"],
			referenced_alerts=[],
			locations=[
				Location(
					episode_key=None,
					event_key="KFWD.TO.W.0015.2024",
					state_fips="48",
					county_fips="113",
					ugc_code="TXC113",
					shape=[Coordinate(latitude=32.9, longitude=-97.4)],
					full_zone_ugc_endpoint="https://api.weather.gov/zones/forecast/TXC113"
				)
			]
		)
		
		# Execute
		result = EventService.update_event_from_alert(cor_alert)
		
		# Assertions
		assert result.nws_alert_id == cor_alert.alert_id  # New alert ID
		assert result.episode_key == existing_event.episode_key  # Preserved
		assert result.event_type == cor_alert.event_type  # From alert
		assert result.locations == cor_alert.locations  # Replaced
		assert result.raw_vtec == cor_alert.raw_vtec  # Replaced
		assert "Corrected Tornado Warning" in result.description
		assert result.is_active == existing_event.is_active  # Preserved
		assert result.property_damage == existing_event.property_damage  # Preserved
		assert result.actual_end_date == existing_event.actual_end_date  # Preserved
		assert existing_event.nws_alert_id in result.previous_ids
	
	@patch('app.services.event_read_service.EventReadService.get_event')
	@patch('app.services.event_update_service.state')
	def test_update_event_upg_message_type(self, mock_state, mock_get_event, existing_event):
		"""Test UPG (Update) message type - replaces entire event."""
		# Setup
		mock_get_event.return_value = existing_event
		mock_state.update_event = Mock()
		
		upg_alert = FilteredNWSAlert(
			alert_id="https://api.weather.gov/alerts/urn:oid:2.49.0.1.840.0.1234567893",
			key="KFWD.TO.W.0015.2024",
			event_type="TOR",
			message_type="UPG",
			is_watch=False,
			is_warning=True,
			severity="Extreme",
			urgency="Immediate",
			certainty="Observed",
			effective="2024-01-15T10:30:00-06:00",
			expires="2024-01-15T12:00:00-06:00",
			expected_end="2024-01-15T12:00:00-06:00",
			headline="Upgraded Tornado Warning",
			description="Upgraded description",
			raw_vtec="/O.UPG.KFWD.TO.W.0015.240115T1030Z-240115T1200Z/",
			affected_zones_ugc_endpoints=["https://api.weather.gov/zones/forecast/TXC113"],
			affected_zones_raw_ugc_codes=["TXC113"],
			referenced_alerts=[],
			locations=[
				Location(
					episode_key=None,
					event_key="KFWD.TO.W.0015.2024",
					state_fips="48",
					county_fips="113",
					ugc_code="TXC113",
					shape=[Coordinate(latitude=32.9, longitude=-97.4)],
					full_zone_ugc_endpoint="https://api.weather.gov/zones/forecast/TXC113"
				)
			]
		)
		
		# Execute
		result = EventService.update_event_from_alert(upg_alert)
		
		# Assertions
		assert result.nws_alert_id == upg_alert.alert_id
		assert result.locations == upg_alert.locations  # Replaced
		assert result.raw_vtec == upg_alert.raw_vtec  # Replaced
		assert "Upgraded Tornado Warning" in result.description
		assert existing_event.nws_alert_id in result.previous_ids
	
	@patch('app.services.event_read_service.EventReadService.get_event')
	@patch('app.services.event_update_service.state')
	def test_update_event_can_message_type(self, mock_state, mock_get_event, existing_event):
		"""Test CAN (Cancel) message type - returns None as it's handled by check_completed_events."""
		# Setup
		mock_get_event.return_value = existing_event
		mock_state.update_event = Mock()
		
		can_alert = FilteredNWSAlert(
			alert_id="https://api.weather.gov/alerts/urn:oid:2.49.0.1.840.0.1234567894",
			key="KFWD.TO.W.0015.2024",
			event_type="TOR",
			message_type="CAN",
			is_watch=False,
			is_warning=True,
			severity="Extreme",
			urgency="Immediate",
			certainty="Observed",
			effective="2024-01-15T10:30:00-06:00",
			expires="2024-01-15T11:00:00-06:00",
			expected_end="2024-01-15T11:00:00-06:00",
			headline="Cancelled",
			description="Warning cancelled",
			raw_vtec="/O.CAN.KFWD.TO.W.0015.240115T1030Z-240115T1100Z/",
			affected_zones_ugc_endpoints=["https://api.weather.gov/zones/forecast/TXC113"],
			affected_zones_raw_ugc_codes=["TXC113"],
			referenced_alerts=[],
			locations=[]
		)
		
		# Execute
		result = EventService.update_event_from_alert(can_alert)
		
		# Assertions - CAN/EXP are now handled by check_completed_events, so this returns None
		assert result is None
		# Should not update event (handled by check_completed_events instead)
		mock_state.update_event.assert_not_called()
	
	@patch('app.services.event_read_service.EventReadService.get_event')
	@patch('app.services.event_update_service.state')
	def test_update_event_exp_message_type(self, mock_state, mock_get_event, existing_event):
		"""Test EXP (Expired) message type - returns None as it's handled by check_completed_events."""
		# Setup
		mock_get_event.return_value = existing_event
		mock_state.update_event = Mock()
		
		exp_alert = FilteredNWSAlert(
			alert_id="https://api.weather.gov/alerts/urn:oid:2.49.0.1.840.0.1234567895",
			key="KFWD.TO.W.0015.2024",
			event_type="TOR",
			message_type="EXP",
			is_watch=False,
			is_warning=True,
			severity="Extreme",
			urgency="Immediate",
			certainty="Observed",
			effective="2024-01-15T10:30:00-06:00",
			expires="2024-01-15T11:00:00-06:00",
			expected_end="2024-01-15T11:00:00-06:00",
			headline="Expired",
			description="Warning expired",
			raw_vtec="/O.EXP.KFWD.TO.W.0015.240115T1030Z-240115T1100Z/",
			affected_zones_ugc_endpoints=["https://api.weather.gov/zones/forecast/TXC113"],
			affected_zones_raw_ugc_codes=["TXC113"],
			referenced_alerts=[],
			locations=[]
		)
		
		# Execute
		result = EventService.update_event_from_alert(exp_alert)
		
		# Assertions - CAN/EXP are now handled by check_completed_events, so this returns None
		assert result is None
		# Should not update event (handled by check_completed_events instead)
		mock_state.update_event.assert_not_called()
	
	@patch('app.services.event_read_service.EventReadService.get_event')
	@patch('app.services.event_update_service.state')
	def test_update_event_merges_locations(self, mock_state, mock_get_event, existing_event):
		"""Test that standard update merges locations without duplicates."""
		# Setup
		mock_get_event.return_value = existing_event
		mock_state.update_event = Mock()
		
		# Create alert with new location
		new_location = Location(
			episode_key=None,
			event_key="KFWD.TO.W.0015.2024",
			state_fips="48",
			county_fips="215",
			ugc_code="TXC215",
			shape=[Coordinate(latitude=33.0, longitude=-97.0)],
			full_zone_ugc_endpoint="https://api.weather.gov/zones/forecast/TXC215"
		)
		
		update_alert = FilteredNWSAlert(
			alert_id="https://api.weather.gov/alerts/urn:oid:2.49.0.1.840.0.1234567896",
			key="KFWD.TO.W.0015.2024",
			event_type="TOR",
			message_type="CON",
			is_watch=False,
			is_warning=True,
			severity="Extreme",
			urgency="Immediate",
			certainty="Observed",
			effective="2024-01-15T10:30:00-06:00",
			expires="2024-01-15T12:00:00-06:00",
			expected_end="2024-01-15T12:00:00-06:00",
			headline="Updated",
			description="Updated",
			raw_vtec="/O.CON.KFWD.TO.W.0015.240115T1030Z-240115T1200Z/",
			affected_zones_ugc_endpoints=["https://api.weather.gov/zones/forecast/TXC215"],
			affected_zones_raw_ugc_codes=["TXC215"],
			referenced_alerts=[],
			locations=[new_location]
		)
		
		# Execute
		result = EventService.update_event_from_alert(update_alert)
		
		# Assertions
		assert len(result.locations) == 2  # Original + new
		ugc_codes = {loc.ugc_code for loc in result.locations}
		assert "TXC113" in ugc_codes
		assert "TXC215" in ugc_codes
	
	@patch('app.services.event_read_service.EventReadService.get_event')
	@patch('app.services.event_update_service.state')
	def test_update_event_no_duplicate_locations(self, mock_state, mock_get_event, existing_event):
		"""Test that duplicate locations (same ugc_code) are not added."""
		# Setup
		mock_get_event.return_value = existing_event
		mock_state.update_event = Mock()
		
		# Create alert with same location as existing
		duplicate_location = Location(
			episode_key=None,
			event_key="KFWD.TO.W.0015.2024",
			state_fips="48",
			county_fips="113",
			ugc_code="TXC113",  # Same as existing
			shape=[Coordinate(latitude=32.8, longitude=-97.5)],
			full_zone_ugc_endpoint="https://api.weather.gov/zones/forecast/TXC113"
		)
		
		update_alert = FilteredNWSAlert(
			alert_id="https://api.weather.gov/alerts/urn:oid:2.49.0.1.840.0.1234567897",
			key="KFWD.TO.W.0015.2024",
			event_type="TOR",
			message_type="CON",
			is_watch=False,
			is_warning=True,
			severity="Extreme",
			urgency="Immediate",
			certainty="Observed",
			effective="2024-01-15T10:30:00-06:00",
			expires="2024-01-15T12:00:00-06:00",
			expected_end="2024-01-15T12:00:00-06:00",
			headline="Updated",
			description="Updated",
			raw_vtec="/O.CON.KFWD.TO.W.0015.240115T1030Z-240115T1200Z/",
			affected_zones_ugc_endpoints=["https://api.weather.gov/zones/forecast/TXC113"],
			affected_zones_raw_ugc_codes=["TXC113"],
			referenced_alerts=[],
			locations=[duplicate_location]
		)
		
		# Execute
		result = EventService.update_event_from_alert(update_alert)
		
		# Assertions
		assert len(result.locations) == 1  # No duplicate added
		assert result.locations[0].ugc_code == "TXC113"
	
	@patch('app.services.event_read_service.EventReadService.get_event')
	@patch('app.services.event_update_service.state')
	def test_update_event_not_found_error(self, mock_state, mock_get_event, update_alert):
		"""Test that NotFoundError is raised when event doesn't exist."""
		# Setup
		from app.exceptions import NotFoundError
		mock_get_event.side_effect = NotFoundError("Event", update_alert.key)
		
		# Execute & Assert
		with pytest.raises(NotFoundError):
			EventService.update_event_from_alert(update_alert)
	
	@patch('app.services.event_read_service.EventReadService.get_event')
	@patch('app.services.event_update_service.state')
	def test_update_event_tracks_previous_ids(self, mock_state, mock_get_event, existing_event, update_alert):
		"""Test that previous alert IDs are tracked correctly."""
		# Setup
		existing_event.previous_ids = ["old-alert-1", "old-alert-2"]
		mock_get_event.return_value = existing_event
		mock_state.update_event = Mock()
		
		# Execute
		result = EventService.update_event_from_alert(update_alert)
		
		# Assertions
		assert len(result.previous_ids) == 3  # 2 old + 1 current
		assert "old-alert-1" in result.previous_ids
		assert "old-alert-2" in result.previous_ids
		assert existing_event.nws_alert_id in result.previous_ids
	
	@patch('app.services.event_read_service.EventReadService.get_event')
	@patch('app.services.event_update_service.state')
	def test_update_event_no_duplicate_previous_id(self, mock_state, mock_get_event, existing_event):
		"""Test that current alert ID is not added to previous_ids if already there."""
		# Setup
		existing_event.previous_ids = [existing_event.nws_alert_id]  # Already in list
		mock_get_event.return_value = existing_event
		mock_state.update_event = Mock()
		
		update_alert = FilteredNWSAlert(
			alert_id="https://api.weather.gov/alerts/urn:oid:2.49.0.1.840.0.1234567898",
			key="KFWD.TO.W.0015.2024",
			event_type="TOR",
			message_type="CON",
			is_watch=False,
			is_warning=True,
			severity="Extreme",
			urgency="Immediate",
			certainty="Observed",
			effective="2024-01-15T10:30:00-06:00",
			expires="2024-01-15T12:00:00-06:00",
			expected_end="2024-01-15T12:00:00-06:00",
			headline="Updated",
			description="Updated",
			raw_vtec="/O.CON.KFWD.TO.W.0015.240115T1030Z-240115T1200Z/",
			affected_zones_ugc_endpoints=[],
			affected_zones_raw_ugc_codes=[],
			referenced_alerts=[],
			locations=[]
		)
		
		# Execute
		result = EventService.update_event_from_alert(update_alert)
		
		# Assertions - should only have one instance of the old alert ID
		assert result.previous_ids.count(existing_event.nws_alert_id) == 1
	
	@patch('app.services.event_read_service.EventReadService.get_event')
	@patch('app.services.event_update_service.state')
	def test_update_event_case_insensitive_message_type(self, mock_state, mock_get_event, existing_event):
		"""Test that message type comparison is case-insensitive."""
		# Setup
		mock_get_event.return_value = existing_event
		mock_state.update_event = Mock()
		
		# Use lowercase message type
		can_alert = FilteredNWSAlert(
			alert_id="https://api.weather.gov/alerts/urn:oid:2.49.0.1.840.0.1234567899",
			key="KFWD.TO.W.0015.2024",
			event_type="TOR",
			message_type="can",  # lowercase
			is_watch=False,
			is_warning=True,
			severity="Extreme",
			urgency="Immediate",
			certainty="Observed",
			effective="2024-01-15T10:30:00-06:00",
			expires="2024-01-15T11:00:00-06:00",
			expected_end="2024-01-15T11:00:00-06:00",
			headline="Cancelled",
			description="Warning cancelled",
			raw_vtec="/O.CAN.KFWD.TO.W.0015.240115T1030Z-240115T1100Z/",
			affected_zones_ugc_endpoints=[],
			affected_zones_raw_ugc_codes=[],
			referenced_alerts=[],
			locations=[]
		)
		
		# Execute
		result = EventService.update_event_from_alert(can_alert)
		
		# Assertions - CAN/EXP are now handled by check_completed_events, so this returns None
		assert result is None
	
	@patch('app.services.event_read_service.EventReadService.get_event')
	@patch('app.services.event_update_service.state')
	def test_update_event_with_missing_expected_end(self, mock_state, mock_get_event, existing_event):
		"""Test update when expected_end is None."""
		# Setup
		mock_get_event.return_value = existing_event
		mock_state.update_event = Mock()
		
		update_alert = FilteredNWSAlert(
			alert_id="https://api.weather.gov/alerts/urn:oid:2.49.0.1.840.0.1234567900",
			key="KFWD.TO.W.0015.2024",
			event_type="TOR",
			message_type="CON",
			is_watch=False,
			is_warning=True,
			severity="Extreme",
			urgency="Immediate",
			certainty="Observed",
			effective="2024-01-15T10:30:00-06:00",
			expires="2024-01-15T12:00:00-06:00",
			expected_end=None,  # Missing
			headline="Updated",
			description="Updated",
			raw_vtec="/O.CON.KFWD.TO.W.0015.240115T1030Z-240115T1200Z/",
			affected_zones_ugc_endpoints=[],
			affected_zones_raw_ugc_codes=[],
			referenced_alerts=[],
			locations=[]
		)
		
		# Execute
		result = EventService.update_event_from_alert(update_alert)
		
		# Assertions
		assert result.expected_end_date is None  # Should handle None gracefully
		# For CAN/EXP, actual_end_date should also be None if expected_end is None
		if update_alert.message_type in ["CAN", "EXP"]:
			# This would be tested in a separate test, but here we're testing CON
			pass


class TestCheckCompletedEvents:
	"""Test cases for EventService.check_completed_events."""
	
	@pytest.fixture
	def active_event_past_end_date(self):
		"""Create an active event past its expected end date."""
		return Event(
			event_key="KFWD.TO.W.0015.2024",
			nws_alert_id="alert-123",
			episode_key=None,
			event_type="TOR",
			hr_event_type="Tornado Warning",
			locations=[],
			start_date=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
			expected_end_date=datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc),  # Past
			actual_end_date=None,
			updated_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
			description="Test",
			is_active=True,
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/",
			previous_ids=[]
		)
	
	@pytest.fixture
	def active_event_future_end_date(self):
		"""Create an active event with future expected end date."""
		future_date = datetime.now(timezone.utc) + timedelta(hours=1)
		return Event(
			event_key="KFWD.TO.W.0016.2024",
			nws_alert_id="alert-456",
			episode_key=None,
			event_type="TOR",
			hr_event_type="Tornado Warning",
			locations=[],
			start_date=datetime.now(timezone.utc),
			expected_end_date=future_date,
			actual_end_date=None,
			updated_at=datetime.now(timezone.utc),
			description="Test",
			is_active=True,
			raw_vtec="/O.NEW.KFWD.TO.W.0016.240115T1000Z-240115T1100Z/",
			previous_ids=[]
		)
	
	@patch('app.services.event_completion_service.state')
	@patch('app.services.event_completion_service.asyncio.run')
	def test_check_completed_events_no_active_events(self, mock_asyncio_run, mock_state):
		"""Test when there are no active events."""
		type(mock_state).active_events = PropertyMock(return_value=[])
		
		EventService.check_completed_events()
		
		mock_asyncio_run.assert_not_called()
	
	@patch('app.services.event_completion_service.state')
	@patch('app.services.event_completion_service.asyncio.run')
	def test_check_completed_events_no_events_past_end_date(self, mock_asyncio_run, mock_state, active_event_future_end_date):
		"""Test when no events are past their expected end date."""
		type(mock_state).active_events = PropertyMock(return_value=[active_event_future_end_date])
		
		EventService.check_completed_events()
		
		mock_asyncio_run.assert_not_called()
	
	@patch('app.services.event_completion_service.state')
	@patch('app.services.event_completion_service.asyncio.run')
	def test_check_completed_events_filters_by_end_date(self, mock_asyncio_run, mock_state, active_event_past_end_date, active_event_future_end_date):
		"""Test that only events past expected end date are checked."""
		type(mock_state).active_events = PropertyMock(return_value=[active_event_past_end_date, active_event_future_end_date])
		
		EventService.check_completed_events()
		
		# Should call asyncio.run
		mock_asyncio_run.assert_called_once()
		# Verify it was called (the coroutine will be passed to asyncio.run)
		assert mock_asyncio_run.called
	
	@patch('app.services.event_completion_service.state')
	@patch('app.services.event_completion_service.NWSClient')
	@patch('app.services.event_completion_service.vtec.get_message_type')
	@patch('app.utils.nws_alert_parser.NWSAlertParser.get_most_recent_alert')
	@patch('app.utils.nws_alert_parser.NWSAlertParser.extract_actual_end_time')
	@pytest.mark.asyncio
	async def test_check_completed_events_can_message_type(self, mock_extract_time, mock_get_alert, mock_get_message_type, mock_client_class, mock_state, active_event_past_end_date):
		"""Test that events with CAN message type are marked inactive."""
		mock_state.update_event = Mock()
		
		# Mock alert data
		alert_data = {
			"features": [{"properties": {"id": "alert-123"}}]
		}
		mock_get_alert.return_value = alert_data
		mock_get_message_type.return_value = "CAN"
		mock_extract_time.return_value = datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc)
		
		mock_client = AsyncMock()
		mock_client.close = AsyncMock()
		mock_client_class.return_value = mock_client
		
		await EventCompletionService._async_check_completed_events([active_event_past_end_date])
		
		# Should update event to inactive
		mock_state.update_event.assert_called_once()
		updated_event = mock_state.update_event.call_args[0][0]
		assert updated_event.is_active is False
		assert updated_event.actual_end_date is not None
	
	@patch('app.services.event_completion_service.state')
	@patch('app.services.event_completion_service.NWSClient')
	@patch('app.services.event_completion_service.vtec.get_message_type')
	@patch('app.utils.nws_alert_parser.NWSAlertParser.get_most_recent_alert')
	@patch('app.utils.nws_alert_parser.NWSAlertParser.extract_actual_end_time')
	@patch('app.services.event_completion_service.settings')
	@pytest.mark.asyncio
	async def test_check_completed_events_timeout_threshold(self, mock_settings, mock_extract_time, mock_get_alert, mock_get_message_type, mock_client_class, mock_state):
		"""Test that events past timeout threshold are marked inactive."""
		mock_settings.event_completion_timeout_minutes = 20
		
		# Create event past expected end date by more than 20 minutes
		past_date = datetime.now(timezone.utc) - timedelta(minutes=25)
		event = Event(
			event_key="KFWD.TO.W.0017.2024",
			nws_alert_id="alert-789",
			episode_key=None,
			event_type="TOR",
			hr_event_type="Tornado Warning",
			locations=[],
			start_date=past_date - timedelta(minutes=30),
			expected_end_date=past_date,
			actual_end_date=None,
			updated_at=past_date,
			description="Test",
			is_active=True,
			raw_vtec="/O.NEW.KFWD.TO.W.0017.240115T1000Z-240115T1100Z/",
			previous_ids=[]
		)
		
		mock_state.update_event = Mock()
		
		alert_data = {
			"features": [{"properties": {"id": "alert-789"}}]
		}
		mock_get_alert.return_value = alert_data
		mock_get_message_type.return_value = "CON"  # Not CAN or EXP
		mock_extract_time.return_value = datetime.now(timezone.utc)
		
		mock_client = AsyncMock()
		mock_client.close = AsyncMock()
		mock_client_class.return_value = mock_client
		
		await EventCompletionService._async_check_completed_events([event])
		
		# Should update event to inactive due to timeout
		mock_state.update_event.assert_called_once()
		updated_event = mock_state.update_event.call_args[0][0]
		assert updated_event.is_active is False
	
	@patch('app.services.event_completion_service.state')
	@patch('app.services.event_completion_service.NWSClient')
	@patch('app.services.event_completion_service.vtec.get_message_type')
	@patch('app.services.event_completion_service.NWSAlertParser.get_most_recent_alert')
	@patch('app.services.event_completion_service.settings')
	@pytest.mark.asyncio
	async def test_check_completed_events_not_past_timeout(self, mock_settings, mock_get_alert, mock_get_message_type, mock_client_class, mock_state):
		"""Test that events not past timeout threshold are not marked inactive."""
		mock_settings.event_completion_timeout_minutes = 20
		
		# Create event past expected end date but not past timeout (10 minutes < 20 minutes)
		past_date = datetime.now(timezone.utc) - timedelta(minutes=10)
		event = Event(
			event_key="KFWD.TO.W.0018.2024",
			nws_alert_id="alert-999",
			episode_key=None,
			event_type="TOR",
			hr_event_type="Tornado Warning",
			locations=[],
			start_date=past_date - timedelta(minutes=30),
			expected_end_date=past_date,
			actual_end_date=None,
			updated_at=past_date,
			description="Test",
			is_active=True,
			raw_vtec="/O.NEW.KFWD.TO.W.0018.240115T1000Z-240115T1100Z/",
			previous_ids=[]
		)
		
		mock_state.update_event = Mock()
		
		alert_data = {
			"features": [{"properties": {"id": "alert-999"}}]
		}
		mock_get_alert.return_value = alert_data
		mock_get_message_type.return_value = "CON"  # Not CAN or EXP
		
		mock_client = AsyncMock()
		mock_client.close = AsyncMock()
		mock_client_class.return_value = mock_client
		
		await EventCompletionService._async_check_completed_events([event])
		
		# Should NOT update event (not past timeout)
		mock_state.update_event.assert_not_called()
	
	@patch('app.services.event_completion_service.state')
	@patch('app.services.event_completion_service.NWSClient')
	@patch('app.services.event_completion_service.NWSAlertParser.get_most_recent_alert')
	@pytest.mark.asyncio
	async def test_check_completed_events_handles_missing_alert(self, mock_get_alert, mock_client_class, mock_state, active_event_past_end_date):
		"""Test handling when alert cannot be retrieved."""
		mock_state.update_event = Mock()
		
		mock_get_alert.return_value = None  # Alert not found
		
		mock_client = AsyncMock()
		mock_client.close = AsyncMock()
		mock_client_class.return_value = mock_client
		
		await EventCompletionService._async_check_completed_events([active_event_past_end_date])
		
		# Should not update event
		mock_state.update_event.assert_not_called()
	
	@patch('app.services.event_completion_service.state')
	@patch('app.services.event_completion_service.NWSClient')
	@patch('app.services.event_completion_service.NWSAlertParser.get_most_recent_alert')
	@pytest.mark.asyncio
	async def test_check_completed_events_handles_exception(self, mock_get_alert, mock_client_class, mock_state, active_event_past_end_date):
		"""Test handling exceptions during processing."""
		mock_state.update_event = Mock()
		
		mock_get_alert.side_effect = Exception("API Error")
		
		mock_client = AsyncMock()
		mock_client.close = AsyncMock()
		mock_client_class.return_value = mock_client
		
		# Should not raise exception, just log and continue
		await EventCompletionService._async_check_completed_events([active_event_past_end_date])
		
		# Should not update event
		mock_state.update_event.assert_not_called()


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


class TestGetEvents:
	"""Test cases for EventService.get_events filtering functionality."""
	
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
		
		result = EventService.get_events()
		
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
		
		result = EventService.get_events(active_only=True)
		
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
		
		result = EventService.get_events(active_only=False)
		
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
		
		result = EventService.get_events(active_only=True)
		
		# Should return empty list
		assert len(result) == 0


class TestConfirmedFunctionality:
	"""Test cases for confirmed field functionality."""
	
	@patch('app.services.event_create_service.state')
	def test_create_event_with_observed_certainty_sets_confirmed_true(self, mock_state):
		"""Test that creating an event with certainty='Observed' sets confirmed=True."""
		mock_state.event_exists.return_value = False
		mock_state.add_event = Mock()
		
		alert = FilteredNWSAlert(
			alert_id="test-alert-1",
			key="KFWD.TO.W.0015.2024",
			event_type="TOR",
			message_type="NEW",
			is_watch=False,
			is_warning=True,
			severity="Extreme",
			urgency="Immediate",
			certainty="Observed",
			effective="2024-01-15T10:00:00-06:00",
			expires="2024-01-15T11:00:00-06:00",
			expected_end="2024-01-15T11:00:00-06:00",
			headline="Test",
			description="Test",
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/",
			affected_zones_ugc_endpoints=[],
			affected_zones_raw_ugc_codes=[],
			referenced_alerts=[],
			locations=[]
		)
		
		result = EventService.create_event_from_alert(alert)
		
		assert result.confirmed is True
	
	@patch('app.services.event_create_service.state')
	def test_create_event_with_non_observed_certainty_sets_confirmed_false(self, mock_state):
		"""Test that creating an event with certainty != 'Observed' sets confirmed=False."""
		mock_state.event_exists.return_value = False
		mock_state.add_event = Mock()
		
		alert = FilteredNWSAlert(
			alert_id="test-alert-1",
			key="KFWD.TO.W.0015.2024",
			event_type="TOR",
			message_type="NEW",
			is_watch=False,
			is_warning=True,
			severity="Extreme",
			urgency="Immediate",
			certainty="Likely",
			effective="2024-01-15T10:00:00-06:00",
			expires="2024-01-15T11:00:00-06:00",
			expected_end="2024-01-15T11:00:00-06:00",
			headline="Test",
			description="Test",
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/",
			affected_zones_ugc_endpoints=[],
			affected_zones_raw_ugc_codes=[],
			referenced_alerts=[],
			locations=[]
		)
		
		result = EventService.create_event_from_alert(alert)
		
		assert result.confirmed is False
	
	@patch('app.services.event_create_service.state')
	def test_create_event_with_case_insensitive_observed_certainty(self, mock_state):
		"""Test that certainty check is case-insensitive."""
		mock_state.event_exists.return_value = False
		mock_state.add_event = Mock()
		
		# Test lowercase
		alert_lower = FilteredNWSAlert(
			alert_id="test-alert-1",
			key="KFWD.TO.W.0015.2024",
			event_type="TOR",
			message_type="NEW",
			is_watch=False,
			is_warning=True,
			severity="Extreme",
			urgency="Immediate",
			certainty="observed",
			effective="2024-01-15T10:00:00-06:00",
			expires="2024-01-15T11:00:00-06:00",
			expected_end="2024-01-15T11:00:00-06:00",
			headline="Test",
			description="Test",
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/",
			affected_zones_ugc_endpoints=[],
			affected_zones_raw_ugc_codes=[],
			referenced_alerts=[],
			locations=[]
		)
		
		result = EventService.create_event_from_alert(alert_lower)
		assert result.confirmed is True
		
		# Test mixed case
		mock_state.event_exists.return_value = False
		alert_mixed = FilteredNWSAlert(
			alert_id="test-alert-2",
			key="KFWD.TO.W.0016.2024",
			event_type="TOR",
			message_type="NEW",
			is_watch=False,
			is_warning=True,
			severity="Extreme",
			urgency="Immediate",
			certainty="OBSERVED",
			effective="2024-01-15T10:00:00-06:00",
			expires="2024-01-15T11:00:00-06:00",
			expected_end="2024-01-15T11:00:00-06:00",
			headline="Test",
			description="Test",
			raw_vtec="/O.NEW.KFWD.TO.W.0016.240115T1000Z-240115T1100Z/",
			affected_zones_ugc_endpoints=[],
			affected_zones_raw_ugc_codes=[],
			referenced_alerts=[],
			locations=[]
		)
		
		result = EventService.create_event_from_alert(alert_mixed)
		assert result.confirmed is True
	
	@patch('app.services.event_read_service.EventReadService.get_event')
	@patch('app.services.event_update_service.state')
	def test_update_event_with_observed_certainty_sets_confirmed_true(self, mock_state, mock_get_event):
		"""Test that updating an event with certainty='Observed' sets confirmed=True."""
		existing_event = Event(
			event_key="KFWD.TO.W.0015.2024",
			nws_alert_id="alert-1",
			event_type="TOR",
			start_date=datetime.now(timezone.utc),
			description="Existing event",
			is_active=True,
			confirmed=False,
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/"
		)
		
		update_alert = FilteredNWSAlert(
			alert_id="alert-2",
			key="KFWD.TO.W.0015.2024",
			event_type="TOR",
			message_type="CON",
			is_watch=False,
			is_warning=True,
			severity="Extreme",
			urgency="Immediate",
			certainty="Observed",
			effective="2024-01-15T10:00:00-06:00",
			expires="2024-01-15T11:00:00-06:00",
			expected_end="2024-01-15T11:00:00-06:00",
			headline="Updated",
			description="Updated description",
			raw_vtec="/O.CON.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/",
			affected_zones_ugc_endpoints=[],
			affected_zones_raw_ugc_codes=[],
			referenced_alerts=[],
			locations=[]
		)
		
		mock_get_event.return_value = existing_event
		mock_state.update_event = Mock()
		
		result = EventService.update_event_from_alert(update_alert)
		
		assert result.confirmed is True
	
	@patch('app.services.event_read_service.EventReadService.get_event')
	@patch('app.services.event_update_service.state')
	def test_update_event_preserves_confirmed_if_already_true(self, mock_state, mock_get_event):
		"""Test that updating an event preserves confirmed=True if already set."""
		existing_event = Event(
			event_key="KFWD.TO.W.0015.2024",
			nws_alert_id="alert-1",
			event_type="TOR",
			start_date=datetime.now(timezone.utc),
			description="Existing event",
			is_active=True,
			confirmed=True,
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/"
		)
		
		update_alert = FilteredNWSAlert(
			alert_id="alert-2",
			key="KFWD.TO.W.0015.2024",
			event_type="TOR",
			message_type="CON",
			is_watch=False,
			is_warning=True,
			severity="Extreme",
			urgency="Immediate",
			certainty="Likely",  # Not observed
			effective="2024-01-15T10:00:00-06:00",
			expires="2024-01-15T11:00:00-06:00",
			expected_end="2024-01-15T11:00:00-06:00",
			headline="Updated",
			description="Updated description",
			raw_vtec="/O.CON.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/",
			affected_zones_ugc_endpoints=[],
			affected_zones_raw_ugc_codes=[],
			referenced_alerts=[],
			locations=[]
		)
		
		mock_get_event.return_value = existing_event
		mock_state.update_event = Mock()
		
		result = EventService.update_event_from_alert(update_alert)
		
		# Should preserve confirmed=True even though new alert is not observed
		assert result.confirmed is True
	
	@patch('app.services.event_read_service.EventReadService.get_event')
	@patch('app.services.event_update_service.state')
	def test_replace_event_with_observed_certainty_sets_confirmed_true(self, mock_state, mock_get_event):
		"""Test that replacing an event (COR/UPG) with certainty='Observed' sets confirmed=True."""
		existing_event = Event(
			event_key="KFWD.TO.W.0015.2024",
			nws_alert_id="alert-1",
			event_type="TOR",
			start_date=datetime.now(timezone.utc),
			description="Existing event",
			is_active=True,
			confirmed=False,
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/"
		)
		
		cor_alert = FilteredNWSAlert(
			alert_id="alert-2",
			key="KFWD.TO.W.0015.2024",
			event_type="TOR",
			message_type="COR",
			is_watch=False,
			is_warning=True,
			severity="Extreme",
			urgency="Immediate",
			certainty="Observed",
			effective="2024-01-15T10:00:00-06:00",
			expires="2024-01-15T11:00:00-06:00",
			expected_end="2024-01-15T11:00:00-06:00",
			headline="Corrected",
			description="Corrected description",
			raw_vtec="/O.COR.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/",
			affected_zones_ugc_endpoints=[],
			affected_zones_raw_ugc_codes=[],
			referenced_alerts=[],
			locations=[]
		)
		
		mock_get_event.return_value = existing_event
		mock_state.update_event = Mock()
		
		result = EventService.update_event_from_alert(cor_alert)
		
		assert result.confirmed is True
	
	@patch('app.services.event_create_service.state')
	def test_create_event_with_empty_certainty_sets_confirmed_false(self, mock_state):
		"""Test that creating an event with empty certainty string sets confirmed=False."""
		mock_state.event_exists.return_value = False
		mock_state.add_event = Mock()
		
		alert = FilteredNWSAlert(
			alert_id="test-alert-1",
			key="KFWD.TO.W.0015.2024",
			event_type="TOR",
			message_type="NEW",
			is_watch=False,
			is_warning=True,
			severity="Extreme",
			urgency="Immediate",
			certainty="",  # Empty string
			effective="2024-01-15T10:00:00-06:00",
			expires="2024-01-15T11:00:00-06:00",
			expected_end="2024-01-15T11:00:00-06:00",
			headline="Test",
			description="Test",
			raw_vtec="/O.NEW.KFWD.TO.W.0015.240115T1000Z-240115T1100Z/",
			affected_zones_ugc_endpoints=[],
			affected_zones_raw_ugc_codes=[],
			referenced_alerts=[],
			locations=[]
		)
		
		result = EventService.create_event_from_alert(alert)
		
		assert result.confirmed is False
