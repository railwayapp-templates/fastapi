"""
Unit tests for ClickHouse transformer.
"""
import pytest
from datetime import datetime, timezone
from app.clickhouse.transformer import ClickHouseTransformer
from app.schemas.event import Event
from app.schemas.location import Location, Coordinate


class TestClickHouseTransformer:
	"""Test suite for ClickHouseTransformer."""
	
	def test_event_to_tuple(self):
		"""Test converting Event to tuple for ClickHouse insertion."""
		event = Event(
			event_key="TEST_KEY",
			nws_alert_id="TEST_ALERT",
			episode_key="TEST_EPISODE",
			event_type="TO",
			hr_event_type="Tornado Warning",
			locations=[],
			start_date=datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.utc),
			expected_end_date=datetime(2024, 1, 15, 15, 30, 0, tzinfo=timezone.utc),
			actual_end_date=None,
			updated_at=datetime(2024, 1, 15, 14, 35, 0, tzinfo=timezone.utc),
			property_damage=50000,
			crops_damage=10000,
			range_miles=2.5,
			description="Test description",
			is_active=True,
			confirmed=True,
			etl_processed=False,
			raw_vtec="/O.NEW.KSBY.TO.W.0123.240115T1430Z-240115T1530Z/",
			office="KSBY",
			previous_ids=["alert1", "alert2"]
		)
		
		result = ClickHouseTransformer.event_to_tuple(event)
		
		# Verify it's a tuple
		assert isinstance(result, tuple)
		
		# Verify tuple length (20 fields)
		assert len(result) == 20
		
		# Verify field values
		assert result[0] == "TEST_KEY"
		assert result[1] == "TEST_ALERT"
		assert result[2] == "TEST_EPISODE"
		assert result[3] == "TO"
		assert result[4] == "Tornado Warning"
		assert result[5] == datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.utc)
		assert result[6] == datetime(2024, 1, 15, 15, 30, 0, tzinfo=timezone.utc)
		assert result[7] is None
		assert result[8] == datetime(2024, 1, 15, 14, 35, 0, tzinfo=timezone.utc)
		assert result[9] == 50000
		assert result[10] == 10000
		assert result[11] == 2.5
		assert result[12] == "Test description"
		assert result[13] == 1  # is_active converted to 1
		assert result[14] == 1  # confirmed converted to 1
		assert result[15] == 1  # etl_processed always set to 1 for ClickHouse insert
		assert result[16] == "/O.NEW.KSBY.TO.W.0123.240115T1430Z-240115T1530Z/"
		assert result[17] == "KSBY"
		assert result[18] == ["alert1", "alert2"]
		assert isinstance(result[19], datetime)  # inserted_at should be current time
	
	def test_event_to_tuple_with_none_values(self):
		"""Test converting Event with None values to tuple."""
		event = Event(
			event_key="TEST_KEY",
			nws_alert_id="TEST_ALERT",
			episode_key=None,
			event_type="TO",
			hr_event_type=None,
			locations=[],
			start_date=datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.utc),
			expected_end_date=None,
			actual_end_date=None,
			updated_at=None,
			property_damage=None,
			crops_damage=None,
			range_miles=None,
			description="Test",
			is_active=False,
			confirmed=False,
			etl_processed=False,
			raw_vtec="TEST",
			office=None,
			previous_ids=[]
		)
		
		result = ClickHouseTransformer.event_to_tuple(event)
		
		assert len(result) == 20
		assert result[2] is None  # episode_key
		assert result[4] is None  # hr_event_type
		assert result[6] is None  # expected_end_date
		assert result[7] is None  # actual_end_date
		assert result[8] is None  # updated_at
		assert result[9] is None  # property_damage
		assert result[10] is None  # crops_damage
		assert result[11] is None  # range_miles
		assert result[13] == 0  # is_active
		assert result[14] == 0  # confirmed
		assert result[15] == 1  # etl_processed always set to 1 for ClickHouse insert
		assert result[17] is None  # office
		assert result[18] == []  # previous_ids
	
	def test_location_to_tuple(self):
		"""Test converting Location to tuple for ClickHouse insertion."""
		location = Location(
			episode_key="TEST_EPISODE",
			event_key="TEST_KEY",
			state_fips="06",
			county_fips="083",
			ugc_code="CAC083",
			full_zone_ugc_endpoint="https://api.weather.gov/zones/county/CAC083",
			full_shape=[
				[
					Coordinate(latitude=35.1234, longitude=-120.5678),
					Coordinate(latitude=35.2345, longitude=-120.6789),
					Coordinate(latitude=35.1234, longitude=-120.5678)
				]
			],
			starting_point=Coordinate(latitude=35.2000, longitude=-120.6500),
			observed_coordinate=Coordinate(latitude=35.2500, longitude=-120.7000)
		)
		
		result = ClickHouseTransformer.location_to_tuple("TEST_KEY", location)
		
		# Verify it's a tuple
		assert isinstance(result, tuple)
		
		# Verify tuple length (12 fields)
		assert len(result) == 12
		
		# Verify field values
		assert result[0] == "TEST_KEY"
		assert result[1] == "TEST_EPISODE"
		assert result[2] == "06"
		assert result[3] == "083"
		assert result[4] == "CAC083"
		assert result[5] == "https://api.weather.gov/zones/county/CAC083"
		assert result[6] == [[(-120.5678, 35.1234), (-120.6789, 35.2345), (-120.5678, 35.1234)]]
		assert result[7] == -120.6500  # starting_point_lon
		assert result[8] == 35.2000  # starting_point_lat
		assert result[9] == -120.7000  # observed_coordinate_lon
		assert result[10] == 35.2500  # observed_coordinate_lat
		assert isinstance(result[11], datetime)  # inserted_at
	
	def test_location_to_tuple_with_none_values(self):
		"""Test converting Location with None values to tuple."""
		location = Location(
			episode_key=None,
			event_key="TEST_KEY",
			state_fips="06",
			county_fips="083",
			ugc_code="CAC083",
			full_zone_ugc_endpoint="https://api.weather.gov/zones/county/CAC083",
			full_shape=None,
			starting_point=None,
			observed_coordinate=None
		)
		
		result = ClickHouseTransformer.location_to_tuple("TEST_KEY", location)
		
		assert len(result) == 12
		assert result[1] is None  # episode_key
		assert result[6] is None  # full_shape
		assert result[7] is None  # starting_point_lon
		assert result[8] is None  # starting_point_lat
		assert result[9] is None  # observed_coordinate_lon
		assert result[10] is None  # observed_coordinate_lat
	
	def test_location_to_tuple_with_empty_full_shape(self):
		"""Test converting Location with empty full_shape list."""
		location = Location(
			episode_key=None,
			event_key="TEST_KEY",
			state_fips="06",
			county_fips="083",
			ugc_code="CAC083",
			full_zone_ugc_endpoint="https://api.weather.gov/zones/county/CAC083",
			full_shape=[],
			starting_point=None,
			observed_coordinate=None
		)
		
		result = ClickHouseTransformer.location_to_tuple("TEST_KEY", location)
		
		# Empty list evaluates to False, so full_shape_ch will be None
		assert result[6] is None
	
	def test_dict_to_event(self):
		"""Test converting dictionary from ClickHouse to Event object."""
		event_dict = {
			'event_key': 'TEST_KEY',
			'nws_alert_id': 'TEST_ALERT',
			'episode_key': 'TEST_EPISODE',
			'event_type': 'TO',
			'hr_event_type': 'Tornado Warning',
			'start_date': datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.utc),
			'expected_end_date': datetime(2024, 1, 15, 15, 30, 0, tzinfo=timezone.utc),
			'actual_end_date': None,
			'updated_at': datetime(2024, 1, 15, 14, 35, 0, tzinfo=timezone.utc),
			'property_damage': 50000,
			'crops_damage': 10000,
			'range_miles': 2.5,
			'description': 'Test description',
			'is_active': 1,
			'confirmed': 1,
			'etl_processed': 0,
			'raw_vtec': '/O.NEW.KSBY.TO.W.0123.240115T1430Z-240115T1530Z/',
			'office': 'KSBY',
			'previous_ids': ['alert1', 'alert2']
		}
		
		locations = []
		result = ClickHouseTransformer.dict_to_event(event_dict, locations)
		
		assert isinstance(result, Event)
		assert result.event_key == 'TEST_KEY'
		assert result.nws_alert_id == 'TEST_ALERT'
		assert result.episode_key == 'TEST_EPISODE'
		assert result.event_type == 'TO'
		assert result.hr_event_type == 'Tornado Warning'
		assert result.locations == []
		assert result.is_active is True
		assert result.confirmed is True
		assert result.etl_processed is False
		assert result.property_damage == 50000
		assert result.previous_ids == ['alert1', 'alert2']
	
	def test_dict_to_location(self):
		"""Test converting dictionary from ClickHouse to Location object."""
		location_dict = {
			'event_key': 'TEST_KEY',
			'episode_key': 'TEST_EPISODE',
			'state_fips': '06',
			'county_fips': '083',
			'ugc_code': 'CAC083',
			'full_zone_ugc_endpoint': 'https://api.weather.gov/zones/county/CAC083',
			'full_shape': [[(-120.5678, 35.1234), (-120.6789, 35.2345)]],
			'starting_point_lon': -120.6500,
			'starting_point_lat': 35.2000,
			'observed_coordinate_lon': -120.7000,
			'observed_coordinate_lat': 35.2500
		}
		
		result = ClickHouseTransformer.dict_to_location(location_dict)
		
		assert isinstance(result, Location)
		assert result.event_key == 'TEST_KEY'
		assert result.episode_key == 'TEST_EPISODE'
		assert result.state_fips == '06'
		assert result.county_fips == '083'
		assert result.ugc_code == 'CAC083'
		assert len(result.full_shape) == 1
		assert len(result.full_shape[0]) == 2
		assert result.full_shape[0][0].latitude == 35.1234
		assert result.full_shape[0][0].longitude == -120.5678
		assert result.starting_point is not None
		assert result.starting_point.latitude == 35.2000
		assert result.starting_point.longitude == -120.6500
		assert result.observed_coordinate is not None
		assert result.observed_coordinate.latitude == 35.2500
		assert result.observed_coordinate.longitude == -120.7000
	
	def test_dict_to_location_with_none_values(self):
		"""Test converting dictionary with None values to Location."""
		location_dict = {
			'event_key': 'TEST_KEY',
			'episode_key': None,
			'state_fips': '06',
			'county_fips': '083',
			'ugc_code': 'CAC083',
			'full_zone_ugc_endpoint': 'https://api.weather.gov/zones/county/CAC083',
			'full_shape': None,
			'starting_point_lon': None,
			'starting_point_lat': None,
			'observed_coordinate_lon': None,
			'observed_coordinate_lat': None
		}
		
		result = ClickHouseTransformer.dict_to_location(location_dict)
		
		assert result.episode_key is None
		assert result.full_shape is None
		assert result.starting_point is None
		assert result.observed_coordinate is None
