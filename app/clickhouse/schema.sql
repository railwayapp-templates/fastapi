-- ClickHouse table creation scripts for disaster events and locations
-- These tables are designed to be flexible for future use cases

-- Create disaster_events table
CREATE TABLE IF NOT EXISTS disaster_events
(
	event_key String,
	nws_alert_id String,
	episode_key Nullable(String),
	event_type String,
	hr_event_type Nullable(String),
	start_date DateTime,
	expected_end_date Nullable(DateTime),
	actual_end_date Nullable(DateTime),
	updated_at Nullable(DateTime),
	property_damage Nullable(Int64),
	crops_damage Nullable(Int64),
	range_miles Nullable(Float64),
	description String,
	is_active UInt8,
	confirmed UInt8,
	etl_processed UInt8,
	raw_vtec String,
	office Nullable(String),
	previous_ids Array(String),
	inserted_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(start_date)
ORDER BY (event_key, start_date)
SETTINGS index_granularity = 8192;

-- Create disaster_locations table
CREATE TABLE IF NOT EXISTS disaster_locations
(
	event_key String,
	episode_key Nullable(String),
	state_fips String,
	county_fips String,
	ugc_code String,
	full_zone_ugc_endpoint String,
	full_shape Array(Array(Tuple(Float64, Float64))),  -- Array of polygons, each polygon is array of (lon, lat) tuples
	starting_point_lon Nullable(Float64),  -- Longitude of starting point
	starting_point_lat Nullable(Float64),  -- Latitude of starting point
	observed_coordinate_lon Nullable(Float64),  -- Longitude of observed coordinate
	observed_coordinate_lat Nullable(Float64),  -- Latitude of observed coordinate
	inserted_at DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(inserted_at)
ORDER BY (event_key, ugc_code, inserted_at)
SETTINGS index_granularity = 8192;
