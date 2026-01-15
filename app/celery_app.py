"""
Celery application configuration for background tasks.
"""
from celery import Celery
from celery.schedules import crontab, schedule
from datetime import timedelta
import os
from app.config import settings
from app.logging_config import setup_logging

# Setup structured JSON logging for Celery (outputs to stdout)
# This must be done before creating the Celery app
log_level = os.getenv("LOG_LEVEL", "INFO")
setup_logging(level=log_level)

# Create Celery app
celery_app = Celery(
	"quantagentic_api",
	broker=settings.celery_broker_url,
	backend=settings.celery_result_backend
)

# Celery configuration
# Note: Celery will use the logging configuration from app.logging_config
# which outputs structured JSON to stdout (not stderr)
celery_app.conf.update(
	task_serializer="json",
	accept_content=["json"],
	result_serializer="json",
	timezone="UTC",
	enable_utc=True,
)

# CeleryBeat schedule
celery_app.conf.beat_schedule = {
	"disaster-polling-agent": {
		"task": "app.tasks.disaster_polling_task",
		"schedule": schedule(run_every=timedelta(minutes=15)),  # Every 15 minutes, runs immediately on startup
	},
	"wildfire-sync": {
		"task": "app.tasks.wildfire_sync_task",
		"schedule": crontab(hour=13, minute=30),  # 8:30 AM EST / 9:30 AM EDT (13:30 UTC)
	},
	"events-confirmation": {
		"task": "app.tasks.events_confirmation_task",
		"schedule": schedule(run_every=timedelta(hours=1)),  # Every hour
	},
	"etl-task": {
		"task": "app.tasks.etl_task",
		"schedule": schedule(run_every=timedelta(hours=6)),  # Every 6 hours
	},
}

celery_app.conf.timezone = "UTC"

# Import tasks to ensure they're registered
# This must be done AFTER celery_app is created
import app.tasks.disaster_polling_task  # noqa: F401
import app.tasks.drought_sync_task  # noqa: F401
import app.tasks.wildfire_sync_task  # noqa: F401
import app.tasks.events_confirmation_task  # noqa: F401
import app.tasks.etl_task  # noqa: F401

