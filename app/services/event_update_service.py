from datetime import datetime, timezone
from typing import List, Optional
from app.utils.event_types import NWS_WARNING_CODES
from app.exceptions import NotFoundError
from app.schemas.event import Event
from app.schemas.location import Location
from app.shared_models.nws_poller_models import FilteredNWSAlert
from app.state import state
from app.utils.datetime_utils import parse_datetime_to_utc
from app.services.event_read_service import EventReadService
from app.utils.vtec import extract_office_from_vtec
import logging

logger = logging.getLogger(__name__)


class EventUpdateService:
	"""Service for Event update operations."""

	@staticmethod
	def update_event_from_alert(updateable_alert: FilteredNWSAlert) -> Optional[Event]:
		"""
		Update an existing event from an updateable alert.
		
		Update logic:
		- If message_type is "COR" or "UPG": Replace entire event with updateable alert metadata
		- If message_type is "CAN" or "EXP": Mark event as inactive and set actual_end_date
		- Otherwise: Merge locations, update description, update expected_end_date
		
		Args:
			updateable_alert: FilteredNWSAlert with update information
		
		Returns:
			Updated Event object or None for CAN/EXP message types
		
		Raises:
			NotFoundError: If event is not found
		"""
		try:
			existing_event = EventReadService.get_event(updateable_alert.key)
			logger.info(f"Updating event {existing_event.event_key} from alert {updateable_alert.alert_id}")
			
			message_type = updateable_alert.message_type.upper()
			previous_ids = existing_event.previous_ids
			if existing_event.nws_alert_id not in previous_ids:
				previous_ids.append(existing_event.nws_alert_id)
			
			# Handle COR and UPG message types - replace entire event
			if message_type in ["COR", "UPG"]:
				logger.info(f"Message type {message_type} detected - replacing entire event")
				updated_event = EventUpdateService._replace_event_with_alert(existing_event, updateable_alert, previous_ids)
			
			# Handle CAN and EXP message types - mark as inactive
			elif message_type in ["CAN", "EXP"]:
				logger.info(f"Message type {message_type} detected, updates for this are handled via checking for completed events")
				return None
			
			# Default update behavior - merge locations, update description and expected_end_date
			else:
				logger.info(f"Standard update for message type {message_type} - merging locations and updating fields")
				updated_event = EventUpdateService._merge_update_event_from_alert(existing_event, updateable_alert, previous_ids)
			
			# Update the event in state
			state.update_event(updated_event)
			logger.info(f"Successfully updated event {updated_event.event_key}")
			return updated_event
			
		except NotFoundError:
			# Re-raise NotFoundError as-is (callers will handle logging)
			raise
		except Exception as e:
			# Use alert key instead of existing_event.event_key in case get_event failed
			event_key = updateable_alert.key if 'existing_event' not in locals() else existing_event.event_key
			logger.error(f"Error updating event {event_key} from alert {updateable_alert.alert_id}: {str(e)}")
			import traceback
			logger.error(traceback.format_exc())
			raise

	@staticmethod
	def _merge_locations(existing_locations: List[Location], new_locations: List[Location]) -> List[Location]:
		"""
		Merge existing and new locations, avoiding duplicates based on ugc_code.
		
		Args:
			existing_locations: List of existing Location objects
			new_locations: List of new Location objects from updateable alert
		
		Returns:
			Combined list of locations with no duplicates
		"""
		# Get set of existing ugc_codes for quick lookup
		existing_ugc_codes = {loc.ugc_code for loc in existing_locations}
		
		# Start with existing locations
		merged_locations = list(existing_locations)
		
		# Add new locations that don't already exist
		for new_loc in new_locations:
			if new_loc.ugc_code not in existing_ugc_codes:
				merged_locations.append(new_loc)
				existing_ugc_codes.add(new_loc.ugc_code)  # Track to avoid duplicates within new_locations
		
		return merged_locations

	@staticmethod
	def _replace_event_with_alert(existing_event: Event, updateable_alert: FilteredNWSAlert, previous_ids: List[str]) -> Event:
		"""
		Replace entire event with updateable alert metadata.
		Used for COR and UPG message types.
		
		Args:
			existing_event: Existing Event object
			updateable_alert: FilteredNWSAlert with replacement information
			previous_ids: List of previous alert IDs
		
		Returns:
			Event object with replaced metadata
		"""
		# Set confirmed=True if certainty is "observed", otherwise preserve existing confirmed status
		confirmed = existing_event.confirmed
		if updateable_alert.certainty and updateable_alert.certainty.lower() == "observed":
			confirmed = True
		# Extract office from raw_vtec
		office = extract_office_from_vtec(updateable_alert.raw_vtec)
		return Event(
			event_key=updateable_alert.key,
			nws_alert_id=updateable_alert.alert_id,  # Always use new alert_id
			episode_key=existing_event.episode_key,  # Preserve episode_key
			event_type=updateable_alert.event_type,
			hr_event_type=NWS_WARNING_CODES.get(updateable_alert.event_type, "UNKNOWN"),
			locations=updateable_alert.locations,
			start_date=parse_datetime_to_utc(updateable_alert.effective) or existing_event.start_date,
			expected_end_date=parse_datetime_to_utc(updateable_alert.expected_end),
			actual_end_date=existing_event.actual_end_date,  # Preserve actual_end_date unless explicitly set
			updated_at=datetime.now(timezone.utc),
			description=f"{updateable_alert.headline or ''}\n\n{updateable_alert.description or ''}",
			is_active=existing_event.is_active,  # Preserve is_active status
			confirmed=confirmed,
			etl_processed=existing_event.etl_processed,  # Preserve etl_processed status
			raw_vtec=updateable_alert.raw_vtec,
			office=office,
			property_damage=existing_event.property_damage,  # Preserve these fields
			crops_damage=existing_event.crops_damage,
			range_miles=existing_event.range_miles,
			previous_ids=previous_ids
		)

	@staticmethod
	def _merge_update_event_from_alert(existing_event: Event, updateable_alert: FilteredNWSAlert, previous_ids: List[str]) -> Event:
		"""
		Merge locations and update description and expected_end_date.
		Default update behavior for standard message types.
		
		Args:
			existing_event: Existing Event object
			updateable_alert: FilteredNWSAlert with update information
			previous_ids: List of previous alert IDs
		
		Returns:
			Event object with merged updates
		"""
		merged_locations = EventUpdateService._merge_locations(existing_event.locations, updateable_alert.locations)
		
		# Build description from alert
		new_description = f"{updateable_alert.headline or ''}\n\n{updateable_alert.description or ''}"
		
		# Set confirmed=True if certainty is "observed", otherwise preserve existing confirmed status
		confirmed = existing_event.confirmed
		if updateable_alert.certainty and updateable_alert.certainty.lower() == "observed":
			confirmed = True
		
		# Extract office from raw_vtec
		office = extract_office_from_vtec(updateable_alert.raw_vtec) or existing_event.office
		
		return Event(
			event_key=existing_event.event_key,
			nws_alert_id=updateable_alert.alert_id,  # Always use new alert_id
			episode_key=existing_event.episode_key,
			event_type=existing_event.event_type,
			hr_event_type=existing_event.hr_event_type,
			locations=merged_locations,
			start_date=existing_event.start_date,  # Keep original start_date
			expected_end_date=parse_datetime_to_utc(updateable_alert.expected_end),
			actual_end_date=existing_event.actual_end_date,
			updated_at=datetime.now(timezone.utc),
			description=new_description,
			is_active=existing_event.is_active,
			confirmed=confirmed,
			etl_processed=existing_event.etl_processed,  # Preserve etl_processed status
			raw_vtec=updateable_alert.raw_vtec,  # Update raw_vtec
			office=office,
			property_damage=existing_event.property_damage,
			crops_damage=existing_event.crops_damage,
			range_miles=existing_event.range_miles,
			previous_ids=previous_ids
		)

	@staticmethod
	def update_event(event: Event) -> Event:
		"""
		Update an existing event directly from an Event object.
		
		This method updates an event with the provided Event object, preserving
		all fields and updating the updated_at timestamp.
		
		Args:
			event: Event object with updated information
		
		Returns:
			Updated Event object with updated_at timestamp set
		
		Raises:
			NotFoundError: If event is not found
		"""
		# Verify event exists
		EventReadService.get_event(event.event_key)
		
		# Update the event with current timestamp
		updated_event = Event(
			event_key=event.event_key,
			nws_alert_id=event.nws_alert_id,
			episode_key=event.episode_key,
			event_type=event.event_type,
			hr_event_type=event.hr_event_type,
			locations=event.locations,
			start_date=event.start_date,
			expected_end_date=event.expected_end_date,
			actual_end_date=event.actual_end_date,
			updated_at=datetime.now(timezone.utc),
			property_damage=event.property_damage,
			crops_damage=event.crops_damage,
			range_miles=event.range_miles,
			description=event.description,
			is_active=event.is_active,
			confirmed=event.confirmed,
			etl_processed=event.etl_processed,
			raw_vtec=event.raw_vtec,
			office=event.office,
			previous_ids=event.previous_ids
		)
		
		state.update_event(updated_event)
		logger.info(f"Successfully updated event {updated_event.event_key} directly from Event object")
		return updated_event

	@staticmethod
	def deactivate_event(event_key: str) -> Event:
		"""
		Deactivate an event by setting is_active=False and actual_end_date to current time.
		
		Args:
			event_key: Key of event to deactivate
		
		Returns:
			Deactivated Event object
		
		Raises:
			NotFoundError: If event is not found
		"""
		existing_event = EventReadService.get_event(event_key)
		
		# Create updated event with is_active=False and actual_end_date set to now
		deactivated_event = Event(
			event_key=existing_event.event_key,
			nws_alert_id=existing_event.nws_alert_id,
			episode_key=existing_event.episode_key,
			event_type=existing_event.event_type,
			hr_event_type=existing_event.hr_event_type,
			locations=existing_event.locations,
			start_date=existing_event.start_date,
			expected_end_date=existing_event.expected_end_date,
			actual_end_date=datetime.now(timezone.utc),
			updated_at=datetime.now(timezone.utc),
			description=existing_event.description,
			is_active=False,
			confirmed=existing_event.confirmed,
			etl_processed=existing_event.etl_processed,
			raw_vtec=existing_event.raw_vtec,
			office=existing_event.office,
			property_damage=existing_event.property_damage,
			crops_damage=existing_event.crops_damage,
			range_miles=existing_event.range_miles,
			previous_ids=existing_event.previous_ids
		)
		
		# Update the event in state
		state.update_event(deactivated_event)
		logger.info(f"Deactivated event {event_key} with actual_end_date={deactivated_event.actual_end_date}")
		return deactivated_event
