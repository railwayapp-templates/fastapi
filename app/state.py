import logging
from typing import List, Optional
from datetime import datetime
from app.schemas.counties import County
from app.schemas.event import Event
from app.schemas.drought import Drought
from app.schemas.wildfire import Wildfire
from app.redis_client import quantagent_redis
logger = logging.getLogger(__name__)

class State:
	"""
	Shared memory class for the entire API and all agents.
	This acts as a singleton state object.
	
	PROPERTY/SETTER PATTERN EXPLANATION:
	------------------------------------
	The @property and @setter decorators allow us to use methods like attributes,
	but with controlled access. Instead of directly accessing `state._active_events`,
	we use `state.active_events` which:
	
	1. GETTER (@property): When you read `state.active_events`, it calls the getter method
	   - Allows validation, logging, or transformation before returning
	   - Example: `events = state.active_events` calls the getter
	
	2. SETTER (@property_name.setter): When you assign `state.active_events = [...]`, 
	   it calls the setter method
	   - Allows validation, type checking, or side effects before setting
	   - Example: `state.active_events = [event1, event2]` calls the setter
	
	Benefits:
	- Encapsulation: Internal storage (_active_events) is protected
	- Validation: Can check types/values before setting
	- Future-proof: Can add logic later without changing calling code
	- Clean API: Looks like attribute access but with method control
	"""
	
	_instance: Optional['State'] = None
	REDIS_EVENT_KEY_PREFIX = "event:"
	REDIS_EPISODE_KEY_PREFIX = "episode:"
	REDIS_COUNTY_KEY_PREFIX = "county:"
	REDIS_DROUGHT_KEY_PREFIX = "drought:"
	REDIS_WILDFIRE_KEY_PREFIX = "wildfire:"
	REDIS_WILDFIRE_LAST_POLL_KEY = "wildfire:last_poll_date"
	REDIS_LSR_KEY_PREFIX = "polled_lsr:"
	def __new__(cls):
		if cls._instance is None:
			cls._instance = super(State, cls).__new__(cls)
			cls._instance._initialized = False
		return cls._instance
	
	def __init__(self):
		if self._initialized:
			return
		
		# Private attributes (prefixed with _) store the actual data
		self._initialized = True
	
	@property
	def events(self) -> List[Event]:
		"""
		Getter for events.
		Fetches all events from Redis with prefix 'event:'.
		Usage: events = state.events
		"""
		event_keys = quantagent_redis.get_all_keys(f"{State.REDIS_EVENT_KEY_PREFIX}*")
		return quantagent_redis.read_all_as_schema(event_keys, Event, "event")

	@property
	def counties(self) -> List[County]:
		"""
		Getter for counties.
		Fetches all counties from Redis with prefix 'county:'.
		Usage: counties = state.counties
		"""
		county_keys = quantagent_redis.get_all_keys(f"{State.REDIS_COUNTY_KEY_PREFIX}*")
		return quantagent_redis.read_all_as_schema(county_keys, County, "county")

	@property
	def active_events(self) -> List[Event]:
		all_events = self.events
		return [event for event in all_events if event.is_active is True]
	
	@property
	def active_and_unconfirmed_events(self) -> List[Event]:
		all_events = self.events
		return [event for event in all_events if event.is_active is True and not event.confirmed]
	
	@property
	def confirmed_inactive_unprocessed_events(self) -> List[Event]:
		"""
		Getter for confirmed, inactive, and unprocessed events (for ETL).
		"""
		all_events = self.events
		return [
			event for event in all_events 
			if event.confirmed is True 
			and event.is_active is False 
			#and event.etl_processed is False
		]
	
	@property
	def polled_lsr_ids(self) -> List[str]:
		"""
		Getter for polled LSR IDs.
		Fetches all polled LSR IDs from Redis with prefix 'polled_lsr:'.
		Usage: polled_ids = state.polled_lsr_ids
		"""
		lsr_keys = quantagent_redis.get_all_keys(f"{State.REDIS_LSR_KEY_PREFIX}*")
		# Extract IDs from keys (format: "polled_lsr:{lsr_id}")
		return [key.replace(State.REDIS_LSR_KEY_PREFIX, "") for key in lsr_keys]
	
	def add_polled_lsr_id(self, lsr_id: str):
		"""
		Add a polled LSR ID to Redis.
		
		Args:
			lsr_id: LSR ID to mark as polled
		"""
		redis_key = f"{State.REDIS_LSR_KEY_PREFIX}{lsr_id}"
		quantagent_redis.create(redis_key, "1")  # Store a simple marker
	
	def is_lsr_polled(self, lsr_id: str) -> bool:
		"""
		Check if an LSR ID has been polled.
		
		Args:
			lsr_id: LSR ID to check
		
		Returns:
			True if LSR has been polled, False otherwise
		"""
		redis_key = f"{State.REDIS_LSR_KEY_PREFIX}{lsr_id}"
		return quantagent_redis.read(redis_key) is not None

	def add_event(self, event: Event):
		"""
		Add an event to both Redis and in-memory collection.
		
		Args:
			event: Event object
		"""
		redis_key = f"{State.REDIS_EVENT_KEY_PREFIX}{event.event_key}"
		quantagent_redis.create(redis_key, event.to_dict())
	
	def remove_event(self, event_key: str):
		"""Remove an event by key."""
		redis_key = f"{State.REDIS_EVENT_KEY_PREFIX}{event_key}"
		quantagent_redis.delete(redis_key)

	def update_event(self, event: Event):
		"""Update an event in both Redis and in-memory collection."""
		redis_key = f"{State.REDIS_EVENT_KEY_PREFIX}{event.event_key}"
		quantagent_redis.update(redis_key, event.to_dict())
	
	def event_exists(self, event_key: str) -> bool:
		"""
		Check if an event exists with the given event_key.
		
		Args:
			event_key: Event key to check
			
		Returns:
			True if an event exists, False otherwise
		"""
		# Check Redis for the event using standardized key creation
		redis_key = f"{State.REDIS_EVENT_KEY_PREFIX}{event_key}"
		event_dict = quantagent_redis.read(redis_key)
		
		if event_dict is None:
			return False
		
		return True

	def get_event(self, event_key: str) -> Optional[Event]:
		"""Get an event by key."""
		redis_key = f"{State.REDIS_EVENT_KEY_PREFIX}{event_key}"
		return quantagent_redis.read_as_schema(redis_key, Event, "event")

	@property
	def droughts(self) -> List[Drought]:
		"""
		Getter for droughts.
		Fetches all droughts from Redis with prefix 'drought:'.
		Usage: droughts = state.droughts
		"""
		drought_keys = quantagent_redis.get_all_keys(f"{State.REDIS_DROUGHT_KEY_PREFIX}*")
		return quantagent_redis.read_all_as_schema(drought_keys, Drought, "drought")

	@property
	def active_droughts(self) -> List[Drought]:
		"""
		Getter for active droughts.
		Fetches all droughts from Redis and filters by is_active=True.
		Usage: active_droughts = state.active_droughts
		"""
		all_droughts = self.droughts
		return [drought for drought in all_droughts if drought.is_active is True]

	def add_drought(self, drought: Drought):
		"""
		Add a drought to both Redis and in-memory collection.
		
		Args:
			drought: Drought object
		"""
		redis_key = f"{State.REDIS_DROUGHT_KEY_PREFIX}{drought.event_key}"
		quantagent_redis.create(redis_key, drought.to_dict())
	
	def remove_drought(self, event_key: str):
		"""Remove a drought by event_key."""
		redis_key = f"{State.REDIS_DROUGHT_KEY_PREFIX}{event_key}"
		quantagent_redis.delete(redis_key)

	def update_drought(self, drought: Drought):
		"""Update a drought in both Redis and in-memory collection."""
		redis_key = f"{State.REDIS_DROUGHT_KEY_PREFIX}{drought.event_key}"
		quantagent_redis.update(redis_key, drought.to_dict())
	
	def active_drought_exists(self, event_key: str) -> bool:
		"""
		Check if a active drought exists with the given event_key.
		
		Args:
			event_key: Event key to check
			
		Returns:
			True if a active drought exists, False otherwise
		"""
		redis_key = f"{State.REDIS_DROUGHT_KEY_PREFIX}{event_key}"
		drought_dict = quantagent_redis.read_as_dict(redis_key, "drought")
		if drought_dict is None or drought_dict.get('is_active', False) is False:
			return False
		
		return True

	def get_drought(self, event_key: str) -> Optional[Drought]:
		"""Get a drought by event_key."""
		redis_key = f"{State.REDIS_DROUGHT_KEY_PREFIX}{event_key}"
		return quantagent_redis.read_as_schema(redis_key, Drought, "drought")

	@property
	def wildfires(self) -> List[Wildfire]:
		"""
		Getter for wildfires.
		Fetches all wildfires from Redis with prefix 'wildfire:'.
		Usage: wildfires = state.wildfires
		"""
		wildfire_keys = quantagent_redis.get_all_keys(f"{State.REDIS_WILDFIRE_KEY_PREFIX}*")
		# Filter out the last_poll_date key
		wildfire_keys = [k for k in wildfire_keys if k != State.REDIS_WILDFIRE_LAST_POLL_KEY]
		return quantagent_redis.read_all_as_schema(wildfire_keys, Wildfire, "wildfire")

	@property
	def active_wildfires(self) -> List[Wildfire]:
		"""
		Getter for active wildfires.
		Fetches all wildfires from Redis and filters by active=True.
		Usage: active_wildfires = state.active_wildfires
		"""
		all_wildfires = self.wildfires
		return [wildfire for wildfire in all_wildfires if wildfire.active is True]

	def add_wildfire(self, wildfire: Wildfire):
		"""
		Add a wildfire to both Redis and in-memory collection.
		
		Args:
			wildfire: Wildfire object
		"""
		redis_key = f"{State.REDIS_WILDFIRE_KEY_PREFIX}{wildfire.event_key}"
		quantagent_redis.create(redis_key, wildfire.to_dict())
	
	def remove_wildfire(self, event_key: str):
		"""Remove a wildfire by event_key."""
		redis_key = f"{State.REDIS_WILDFIRE_KEY_PREFIX}{event_key}"
		quantagent_redis.delete(redis_key)

	def update_wildfire(self, wildfire: Wildfire):
		"""Update a wildfire in both Redis and in-memory collection."""
		redis_key = f"{State.REDIS_WILDFIRE_KEY_PREFIX}{wildfire.event_key}"
		quantagent_redis.update(redis_key, wildfire.to_dict())
	
	def wildfire_exists(self, event_key: str) -> bool:
		"""
		Check if a wildfire exists with the given event_key.
		
		Args:
			event_key: Event key to check
			
		Returns:
			True if a wildfire exists, False otherwise
		"""
		redis_key = f"{State.REDIS_WILDFIRE_KEY_PREFIX}{event_key}"
		wildfire_dict = quantagent_redis.read_as_dict(redis_key, "wildfire")
		return wildfire_dict is not None
	
	def get_wildfire(self, event_key: str) -> Optional[Wildfire]:
		"""Get a wildfire by event_key."""
		redis_key = f"{State.REDIS_WILDFIRE_KEY_PREFIX}{event_key}"
		return quantagent_redis.read_as_schema(redis_key, Wildfire, "wildfire")
	
	def get_wildfire_by_arcgis_id(self, arcgis_id: str) -> Optional[Wildfire]:
		"""
		Get a wildfire by arcgis_id.
		
		Args:
			arcgis_id: ArcGIS OBJECTID
		
		Returns:
			Wildfire object if found, None otherwise
		"""
		all_wildfires = self.wildfires
		for wildfire in all_wildfires:
			if wildfire.arcgis_id == arcgis_id:
				return wildfire
		return None
	
	def get_wildfire_last_poll_date(self) -> Optional[datetime]:
		"""
		Get the last poll date for wildfires.
		
		Returns:
			datetime object if found, None otherwise
		"""
		value = quantagent_redis.read(State.REDIS_WILDFIRE_LAST_POLL_KEY)
		if value is None:
			return None
		# Value is stored as ISO format string from set_wildfire_last_poll_date
		try:
			return datetime.fromisoformat(value.replace('Z', '+00:00'))
		except (ValueError, AttributeError):
			logger.warning(f"Failed to parse wildfire last poll date: {value}")
			return None
	
	def set_wildfire_last_poll_date(self, poll_date: datetime):
		"""
		Set the last poll date for wildfires.
		
		Args:
			poll_date: datetime object representing the last poll date
		"""
		quantagent_redis.create(State.REDIS_WILDFIRE_LAST_POLL_KEY, poll_date.isoformat())

# Global state instance
state = State()

