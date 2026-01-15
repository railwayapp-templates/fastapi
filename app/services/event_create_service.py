from datetime import datetime, timezone
from app.utils.event_types import NWS_WARNING_CODES
from app.exceptions.base import ConflictError
from app.schemas.event import Event
from app.shared_models.nws_poller_models import FilteredNWSAlert
from app.state import state
from app.utils.datetime_utils import parse_datetime_to_utc
from app.utils.vtec import extract_office_from_vtec
import logging

logger = logging.getLogger(__name__)


class EventCreateService:
	"""Service for Event creation operations."""

	@staticmethod
	def create_event_from_alert(alert: FilteredNWSAlert) -> Event:
		"""
		Create an event from a FilteredNWSAlert.
		
		Args:
			alert: FilteredNWSAlert object
		
		Returns:
			Created Event object
		
		Raises:
			ConflictError: If event with key already exists
		"""
		try:
			logger.info(f"Processing alert {alert.alert_id} with key {alert.key}")
			if state.event_exists(alert.key):
				raise ConflictError(f"Event with key: `{alert.key}` already exists, did we misclassify the alert?")
			# Set confirmed=True if certainty is "observed" (case-insensitive)
			confirmed = alert.certainty.lower() == "observed" if alert.certainty else False
			# Extract office from raw_vtec
			office = extract_office_from_vtec(alert.raw_vtec)
			event = Event(
				event_key=alert.key,
				nws_alert_id=alert.alert_id,
				episode_key=None,
				event_type=alert.event_type,
				hr_event_type=NWS_WARNING_CODES.get(alert.event_type, "UNKNOWN"),
				locations=alert.locations,
				start_date=parse_datetime_to_utc(alert.effective) or datetime.now(timezone.utc),
				expected_end_date=parse_datetime_to_utc(alert.expected_end),
				updated_at=datetime.now(timezone.utc),
				description=f"{alert.headline or ''}\n\n{alert.description or ''}",
				is_active=True,
				confirmed=confirmed,
				etl_processed=False,
				raw_vtec=alert.raw_vtec,
				office=office,
				previous_ids=[]
			)
			state.add_event(event)
			return event
		except ConflictError as e:
			# Re-raise as callers will handle logging for this case.
			raise
		except Exception as e:
			logger.error(f"Error processing alert {alert.alert_id}: {str(e)}")
			import traceback
			logger.error(traceback.format_exc())
			raise
