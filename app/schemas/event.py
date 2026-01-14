from typing import Optional, List
from datetime import datetime
from app.schemas.base import BaseSchema
from app.schemas.location import Location

class Event(BaseSchema):
	# Internal key used to identify unique events. Comprised of the OFFICE + PHENOMENA + SIGNIFICANCE + ETN + YEAR from a VTEC string.
	event_key: str
	# Unique identifier for the alert from the NWS API.
	nws_alert_id: str
	# Unique identifier for the episode that the event is part of.
	episode_key: Optional[str] = None
	# The event type code from the NWS API.
	event_type: str
	# The human-readable event type from the NWS API.
	hr_event_type: Optional[str] = None
	# The locations that the event is affecting.
	locations: List[Location] = []
	# The start date of the event.
	start_date: datetime
	# The expected end date of the event.
	expected_end_date: Optional[datetime] = None
	# The actual end date of the event.
	actual_end_date: Optional[datetime] = None
	# The date and time the event was last updated.
	updated_at: Optional[datetime] = None
	# The property damage of the event.
	property_damage: Optional[int] = None
	# The crops damage of the event.
	crops_damage: Optional[int] = None
	# The range miles of the event.
	range_miles: Optional[float] = None
	# The headline + description of the event.
	description: str
	# Whether or not the event is active.
	is_active: bool = True
	# Whether or not we have proof that the event actually occurred.
	confirmed: bool = False
	# Whether or not the event has been processed by the ETL job.
	etl_processed: bool = False
	# The raw VTEC string from the NWS API.
	raw_vtec: str
	# The NWS office code (e.g., "KSBY", "KMTR") extracted from raw_vtec.
	office: Optional[str] = None
	# The previous alert IDs that have been used to update this event.
	previous_ids: List[str] = []