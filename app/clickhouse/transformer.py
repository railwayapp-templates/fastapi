"""
Transformers for converting between ClickHouse data formats and Python objects.
"""
from typing import Dict, Any, List
from datetime import datetime, timezone
from app.schemas.event import Event
from app.schemas.location import Location, Coordinate


class ClickHouseTransformer:
	"""Transformers for ClickHouse data conversion."""
	
	@staticmethod
	def event_to_tuple(event: Event) -> tuple:
		"""
		Convert Event object to tuple for ClickHouse insertion.
		Tuple order matches the disaster_events table schema.
		
		Note: etl_processed is always set to 1 in the tuple, as this transformer
		is used when inserting events into ClickHouse (marking them as processed).
		
		Args:
			event: Event object to convert
		
		Returns:
			Tuple ready for ClickHouse insertion in schema order:
			(event_key, nws_alert_id, episode_key, event_type, hr_event_type,
			 start_date, expected_end_date, actual_end_date, updated_at,
			 property_damage, crops_damage, range_miles, description,
			 is_active, confirmed, etl_processed (always 1), raw_vtec, office,
			 previous_ids, inserted_at)
		"""
		return (
			event.event_key,
			event.nws_alert_id,
			event.episode_key,
			event.event_type,
			event.hr_event_type,
			event.start_date,
			event.expected_end_date,
			event.actual_end_date,
			event.updated_at,
			event.property_damage,
			event.crops_damage,
			event.range_miles,
			event.description,
			1 if event.is_active else 0,
			1 if event.confirmed else 0,
			1,
			event.raw_vtec,
			event.office,
			event.previous_ids,
			datetime.now(timezone.utc)
		)
	
	@staticmethod
	def dict_to_event(event_dict: Dict[str, Any], locations: List[Location]) -> Event:
		"""
		Convert dictionary from ClickHouse to Event object.
		
		Args:
			event_dict: Dictionary from ClickHouse query
			locations: List of Location objects for this event
		
		Returns:
			Event object
		"""
		return Event(
			event_key=event_dict['event_key'],
			nws_alert_id=event_dict['nws_alert_id'],
			episode_key=event_dict.get('episode_key'),
			event_type=event_dict['event_type'],
			hr_event_type=event_dict.get('hr_event_type'),
			locations=locations,
			start_date=event_dict['start_date'],
			expected_end_date=event_dict.get('expected_end_date'),
			actual_end_date=event_dict.get('actual_end_date'),
			updated_at=event_dict.get('updated_at'),
			property_damage=event_dict.get('property_damage'),
			crops_damage=event_dict.get('crops_damage'),
			range_miles=event_dict.get('range_miles'),
			description=event_dict['description'],
			is_active=bool(event_dict.get('is_active', 0)),
			confirmed=bool(event_dict.get('confirmed', 0)),
			etl_processed=bool(event_dict.get('etl_processed', 0)),
			raw_vtec=event_dict['raw_vtec'],
			office=event_dict.get('office'),
			previous_ids=event_dict.get('previous_ids', [])
		)
	
	@staticmethod
	def dict_to_location(location_dict: Dict[str, Any]) -> Location:
		"""
		Convert dictionary from ClickHouse to Location object.
		
		Args:
			location_dict: Dictionary from ClickHouse query
		
		Returns:
			Location object
		"""
		# Convert full_shape from ClickHouse format
		full_shape = None
		if location_dict.get('full_shape'):
			full_shape = []
			for polygon_ch in location_dict['full_shape']:
				polygon = [Coordinate(latitude=lat, longitude=lon) for lon, lat in polygon_ch]
				full_shape.append(polygon)
		
		# Convert starting_point from separate lon/lat fields
		starting_point = None
		if location_dict.get('starting_point_lon') is not None and location_dict.get('starting_point_lat') is not None:
			lon = location_dict['starting_point_lon']
			lat = location_dict['starting_point_lat']
			starting_point = Coordinate(latitude=lat, longitude=lon)
		
		# Convert observed_coordinate from separate lon/lat fields
		observed_coordinate = None
		if location_dict.get('observed_coordinate_lon') is not None and location_dict.get('observed_coordinate_lat') is not None:
			lon = location_dict['observed_coordinate_lon']
			lat = location_dict['observed_coordinate_lat']
			observed_coordinate = Coordinate(latitude=lat, longitude=lon)
		
		return Location(
			episode_key=location_dict.get('episode_key'),
			event_key=location_dict['event_key'],
			state_fips=location_dict['state_fips'],
			county_fips=location_dict['county_fips'],
			ugc_code=location_dict['ugc_code'],
			full_shape=full_shape,
			full_zone_ugc_endpoint=location_dict['full_zone_ugc_endpoint'],
			starting_point=starting_point,
			observed_coordinate=observed_coordinate
		)
	
	@staticmethod
	def location_to_tuple(event_key: str, location: Location) -> tuple:
		"""
		Convert Location object to tuple for ClickHouse insertion.
		Tuple order matches the disaster_locations table schema.
		
		Args:
			event_key: Event key this location belongs to
			location: Location object to convert
		
		Returns:
			Tuple ready for ClickHouse insertion in schema order:
			(event_key, episode_key, state_fips, county_fips, ugc_code,
			 full_zone_ugc_endpoint, full_shape, starting_point_lon,
			 starting_point_lat, observed_coordinate_lon, observed_coordinate_lat,
			 inserted_at)
		"""
		# Convert full_shape (List[List[Coordinate]]) to ClickHouse format
		# ClickHouse expects Array(Array(Tuple(Float64, Float64)))
		full_shape_ch = None
		if location.full_shape:
			full_shape_ch = []
			for polygon in location.full_shape:
				polygon_ch = [(coord.longitude, coord.latitude) for coord in polygon]
				full_shape_ch.append(polygon_ch)
		
		# Convert starting_point Coordinate to separate lon/lat fields
		starting_point_lon = None
		starting_point_lat = None
		if location.starting_point:
			starting_point_lon = location.starting_point.longitude
			starting_point_lat = location.starting_point.latitude
		
		# Convert observed_coordinate Coordinate to separate lon/lat fields
		observed_coordinate_lon = None
		observed_coordinate_lat = None
		if location.observed_coordinate:
			observed_coordinate_lon = location.observed_coordinate.longitude
			observed_coordinate_lat = location.observed_coordinate.latitude
		
		return (
			event_key,
			location.episode_key,
			location.state_fips,
			location.county_fips,
			location.ugc_code,
			location.full_zone_ugc_endpoint,
			full_shape_ch,
			starting_point_lon,
			starting_point_lat,
			observed_coordinate_lon,
			observed_coordinate_lat,
			datetime.now(timezone.utc)
		)