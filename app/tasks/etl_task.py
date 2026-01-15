"""
Celery task for ETL job that syncs confirmed, inactive, unprocessed events to ClickHouse.
"""
from app.celery_app import celery_app
from app.state import state
from app.clickhouse import ClickHouseClient
from app.schemas.event import Event
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.etl_task", bind=True, max_retries=3)
def etl_task(self):
	"""
	Celery task that syncs confirmed, inactive, unprocessed events to ClickHouse.
	Runs every 6 hours via CeleryBeat schedule.
	
	The task:
	- Fetches all confirmed, inactive, unprocessed events
	- Batch inserts them to ClickHouse (with idempotency check)
	- Marks events as etl_processed=True after successful insertion
	
	Returns:
		Dictionary with summary of ETL results
	"""
	logger.info("=" * 80)
	logger.info("ETL TASK STARTED")
	logger.info("=" * 80)
	
	try:
		# Get events to process
		events_to_process = state.confirmed_inactive_unprocessed_events
		
		if not events_to_process:
			logger.info("No confirmed, inactive, unprocessed events to sync to ClickHouse")
			return {
				"events_processed": 0,
				"events_synced": 0,
				"events_failed": 0,
				"message": "No events to process"
			}
		
		logger.info(f"Found {len(events_to_process)} events to sync to ClickHouse")
		
		# Initialize ClickHouse client
		ch_client = ClickHouseClient()
		
		# Process events in batches with idempotency
		events_synced = 0
		events_failed = 0
		events_skipped = 0
		
		# Filter out events that already exist in ClickHouse (idempotency)
		events_to_insert = []
		for event in events_to_process:
			try:
				if ch_client.check_event_exists(event.event_key):
					logger.debug(f"Event {event.event_key} already exists in ClickHouse, skipping (idempotency)")
					events_skipped += 1
					# Still mark as processed since it's already in ClickHouse
					_mark_event_as_processed(event)
				else:
					events_to_insert.append(event)
			except Exception as e:
				logger.error(f"Error checking if event {event.event_key} exists in ClickHouse: {str(e)}")
				# Continue processing other events
				events_failed += 1
		
		# Batch insert events that don't exist yet
		if events_to_insert:
			try:
				ch_client.write_events_batch(events_to_insert)
				logger.info(f"Successfully batch inserted {len(events_to_insert)} events to ClickHouse")
				
				# Mark all successfully inserted events as processed
				for event in events_to_insert:
					try:
						_mark_event_as_processed(event)
						events_synced += 1
					except Exception as e:
						logger.error(f"Error marking event {event.event_key} as processed: {str(e)}")
						events_failed += 1
						
			except Exception as e:
				logger.error(f"Error batch inserting events to ClickHouse: {str(e)}")
				import traceback
				logger.error(traceback.format_exc())
				# Don't mark any events as processed if batch insert failed
				events_failed += len(events_to_insert)
		
		result = {
			"events_processed": len(events_to_process),
			"events_synced": events_synced,
			"events_skipped": events_skipped,
			"events_failed": events_failed,
			"message": f"ETL completed: {events_synced} synced, {events_skipped} skipped, {events_failed} failed"
		}
		
		logger.info("=" * 80)
		logger.info(f"ETL TASK COMPLETED: {result}")
		logger.info("=" * 80)
		
		return result
		
	except Exception as e:
		logger.error("=" * 80)
		logger.error(f"ETL task FAILED: {str(e)}")
		logger.error(f"Exception type: {type(e).__name__}")
		logger.error("Full traceback:")
		import traceback
		logger.error(traceback.format_exc())
		logger.error("=" * 80)
		# Retry with exponential backoff
		raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


def _mark_event_as_processed(event: Event):
	"""
	Mark an event as ETL processed by updating etl_processed=True.
	
	Args:
		event: Event object to mark as processed
	"""
	from app.state import state
	
	# Create updated event with etl_processed=True
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
		description=event.description,
		is_active=event.is_active,
		confirmed=event.confirmed,
		etl_processed=True,  # Mark as processed
		raw_vtec=event.raw_vtec,
		office=event.office,
		property_damage=event.property_damage,
		crops_damage=event.crops_damage,
		range_miles=event.range_miles,
		previous_ids=event.previous_ids
	)
	
	state.update_event(updated_event)
	logger.debug(f"Marked event {event.event_key} as ETL processed")
