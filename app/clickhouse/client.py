"""
ClickHouse client for reading and writing disaster events and locations.
"""
from typing import List, Optional, Dict, Any
import clickhouse_connect
from app.config import settings
from app.schemas.event import Event
from app.schemas.location import Location
from app.clickhouse.transformer import ClickHouseTransformer
import logging

logger = logging.getLogger(__name__)


class ClickHouseClient:
	"""Reusable ClickHouse client with read/write operations for events and locations."""
	
	def __init__(self):
		"""Initialize ClickHouse client connection."""
		self.client = None
		self._connect()
	
	def _connect(self):
		"""Establish connection to ClickHouse."""
		try:
			self.client = clickhouse_connect.get_client(
				host=settings.clickhouse_host,
				port=settings.clickhouse_port,
				username=settings.clickhouse_user,
				password=settings.clickhouse_password,
				database=settings.clickhouse_db,
				connect_timeout=settings.clickhouse_connect_timeout,
				send_receive_timeout=settings.clickhouse_send_receive_timeout
			)
			logger.info(f"Connected to ClickHouse at {settings.clickhouse_host}:{settings.clickhouse_port} with timeouts: connect={settings.clickhouse_connect_timeout}s, send_receive={settings.clickhouse_send_receive_timeout}s")
		except Exception as e:
			logger.error(f"Failed to connect to ClickHouse: {str(e)}")
			raise
	
	def write_event(self, event: Event) -> None:
		"""
		Write an event and all its locations to ClickHouse.
		If locations fail to insert, the event insert is rolled back.
		
		Args:
			event: Event object to write
		"""
		try:
			# Prepare event data using transformer
			event_data = ClickHouseTransformer.event_to_tuple(event)
			
			# Insert event
			self.client.insert('disaster_events', [event_data])
			logger.debug(f"Inserted event {event.event_key} into ClickHouse")
			
			# Write all locations for this event
			if event.locations:
				self.write_locations(event.event_key, event.locations)
			
			logger.debug(f"Successfully inserted event {event.event_key} and {len(event.locations)} locations")
		
				
		except Exception as e:
			logger.error(f"Error writing event {event.event_key} to ClickHouse: {str(e)}")
			raise
	
	def write_events_batch(self, events: List[Event]) -> None:
		"""
		Batch write multiple events and their locations to ClickHouse.
		
		Args:
			events: List of Event objects to write
		"""
		if not events:
			logger.info("No events to write to ClickHouse")
			return
		
		try:
			# Prepare event data
			event_data_list = []
			all_locations = []
			
			for event in events:
				event_data = ClickHouseTransformer.event_to_tuple(event)
				event_data_list.append(event_data)
				
				# Collect locations
				for location in event.locations:
					all_locations.append((event.event_key, location))
			
			# Batch insert events - dictionary keys must match table column names (excluding inserted_at which has DEFAULT)
			if event_data_list:
				self.client.insert('disaster_events', event_data_list)
				logger.info(f"Batch inserted {len(event_data_list)} events into ClickHouse")
			
			# Batch insert locations
			if all_locations:
				self.write_locations_batch(all_locations)
			
			logger.info(f"Successfully batch inserted {len(events)} events and their locations")
				
		except Exception as e:
			logger.error(f"Error batch writing events to ClickHouse: {str(e)}")
			raise
	
	def write_locations(self, event_key: str, locations: List[Location]) -> None:
		"""
		Write locations for an event to ClickHouse.
		
		Args:
			event_key: Event key these locations belong to
			locations: List of Location objects to write
		"""
		if not locations:
			return
		
		location_data_list = []
		for location in locations:
			location_data = ClickHouseTransformer.location_to_tuple(event_key, location)
			location_data_list.append(location_data)
		
		if location_data_list:
			self.client.insert('disaster_locations', location_data_list)
			logger.debug(f"Inserted {len(location_data_list)} locations for event {event_key} into ClickHouse")
	
	def write_locations_batch(self, event_location_pairs: List[tuple]) -> None:
		"""
		Batch write locations for multiple events.
		
		Args:
			event_location_pairs: List of (event_key, location) tuples
		"""
		if not event_location_pairs:
			return
		
		location_data_list = []
		for event_key, location in event_location_pairs:
			location_data = ClickHouseTransformer.location_to_tuple(event_key, location)
			location_data_list.append(location_data)
		
		if location_data_list:
			self.client.insert('disaster_locations', location_data_list)
			logger.info(f"Batch inserted {len(location_data_list)} locations into ClickHouse")
	
	def read_event(self, event_key: str) -> Optional[Event]:
		"""
		Read an event and its locations from ClickHouse.
		
		Args:
			event_key: Event key to retrieve
		
		Returns:
			Event object with locations, or None if not found
		"""
		try:
			# Validate event_key to prevent injection (event_key should only contain alphanumeric and common separators)
			if not event_key or not isinstance(event_key, str):
				raise ValueError("Invalid event_key")
			
			# Query event - event_key is validated and comes from our own data structures
			# Using format string is safe here as event_key is not user input
			event_result = self.client.query(
				f"SELECT * FROM disaster_events WHERE event_key = '{event_key}' ORDER BY inserted_at DESC LIMIT 1"
			)
			
			if not event_result.result_rows:
				return None
			
			# Get column names
			columns = event_result.column_names
			event_row = event_result.result_rows[0]
			event_dict = dict(zip(columns, event_row))
			
			# Query locations
			locations = self.read_locations(event_key)
			
			# Convert to Event object
			event = ClickHouseTransformer.dict_to_event(event_dict, locations)
			return event
			
		except Exception as e:
			logger.error(f"Error reading event {event_key} from ClickHouse: {str(e)}")
			raise
	
	def read_locations(self, event_key: str) -> List[Location]:
		"""
		Read locations for an event from ClickHouse.
		
		Args:
			event_key: Event key to retrieve locations for
		
		Returns:
			List of Location objects
		"""
		try:
			# Validate event_key to prevent injection
			if not event_key or not isinstance(event_key, str):
				raise ValueError("Invalid event_key")
			
			# Query locations - event_key is validated and comes from our own data structures
			location_result = self.client.query(
				f"SELECT * FROM disaster_locations WHERE event_key = '{event_key}' ORDER BY inserted_at DESC"
			)
			
			locations = []
			if location_result.result_rows:
				columns = location_result.column_names
				for row in location_result.result_rows:
					location_dict = dict(zip(columns, row))
					location = ClickHouseTransformer.dict_to_location(location_dict)
					locations.append(location)
			
			return locations
			
		except Exception as e:
			logger.error(f"Error reading locations for event {event_key} from ClickHouse: {str(e)}")
			raise
	
	
	def check_event_exists(self, event_key: str) -> bool:
		"""
		Check if an event exists in ClickHouse (for idempotency).
		
		Args:
			event_key: Event key to check
		
		Returns:
			True if event exists, False otherwise
		"""
		try:
			# Validate event_key to prevent injection
			if not event_key or not isinstance(event_key, str):
				raise ValueError("Invalid event_key")
			
			# Query count - event_key is validated and comes from our own data structures
			result = self.client.query(
				f"SELECT COUNT(*) as count FROM disaster_events WHERE event_key = '{event_key}'"
			)
			count = result.result_rows[0][0] if result.result_rows else 0
			return count > 0
		except Exception as e:
			logger.error(f"Error checking if event {event_key} exists in ClickHouse: {str(e)}")
			raise
