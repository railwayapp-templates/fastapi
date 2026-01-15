---
title: QuantAgentic API
description: FastAPI server with Redis, CrewAI, and disaster management
tags:
  - fastapi
  - hypercorn
  - python
  - redis
  - crewai
  - celery
---

# QuantAgentic API

A FastAPI-based API for managing disaster events with AI agents powered by CrewAI. Features automated background workers that poll the National Weather Service (NWS) API and intelligently classify alerts into events.


## ✨ Features

- **FastAPI** with async endpoints
- **Redis** for data persistence and Celery task queue
- **CrewAI** for AI agent orchestration with structured outputs
- **Celery & CeleryBeat** for background task processing
- **Docker Compose** for local Redis setup
- **Multi-Source Disaster Data Integration**:
  - **NWS API Integration** - National Weather Service alerts (tornadoes, floods, severe weather, etc.)
  - **ArcGIS Wildfire API** - Real-time wildfire tracking from USGS
  - **Drought Monitor API** - US Drought Monitor data for tracking drought conditions
- **Shared state management** for API and agents
- **Automated Background Workers**:
  - **Disaster Polling Agent** - Processes NWS alerts every 5 minutes
  - **Event Confirmation Task** - Confirms events using Local Storm Reports (LSRs)
  - **Wildfire Sync Task** - Syncs wildfire data from ArcGIS API
  - **Drought Sync Task** - Syncs drought data from US Drought Monitor
- **VTEC Key Generation** for unique alert identification
- **Event Lifecycle Management** - Automatic creation, updates, and completion of disaster events

## 🚀 Getting Started (Mac)

### Prerequisites

- Python 3.9+ (check with `python3 --version`)
- Docker Desktop for Mac (for Redis) - **must be running before starting Redis**
- pip (Python package manager)

### Installation Steps

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone <repository-url>
   cd quantagentic_api
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Start Redis using Docker Compose**:
   
   **Important**: Make sure Docker Desktop is running before executing this command.
   
   ```bash
   docker-compose up -d
   ```
   
   Note: The first time you run this, Docker will download the Redis image, which may take a minute or two.
   
   This will start Redis on `localhost:6379`. To verify it's running:
   ```bash
   docker-compose ps
   ```
   
   If you see an error about Docker daemon not running, start Docker Desktop and wait a few seconds, then try again.

5. **Set up environment variables**:
   
   Create a `.env` file from the example template:
   ```bash
   cp .env.example .env
   ```
   
   Then edit `.env` and set your `GEMINI_API_KEY`:
   ```bash
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ```
   
   The `.env` file is gitignored and will not be committed. All other variables have sensible defaults.
   
   **Required for disaster polling agent**:
   - `GEMINI_API_KEY` - Your Gemini API key
   
   **Required for ETL to ClickHouse**:
   - `CH_HOST` - ClickHouse host (default: `localhost`)
   - `CH_PORT` - ClickHouse port (default: `8123`)
   - `CH_USER` - ClickHouse username (default: `default`)
   - `CH_PASSWORD` - ClickHouse password (default: empty string)
   - `CH_DB` - ClickHouse database name (default: `default`)
   - `IS_PR_ENV` - If `true`, appends `_dev` to database name (default: `false`)
   
   **Optional variables** (with defaults):
   - `REDIS_HOST` - Redis host (default: `localhost`)
   - `REDIS_PORT` - Redis port (default: `6379`)
   - `REDIS_DB` - Redis database number (default: `0`)
   - `REDIS_PASSWORD` - Redis password (default: `None`)
   - `GEMINI_MODEL` - Gemini model (default: `gemini/gemini-3-pro-preview`)
   - `EXECUTOR_MAX_RETRIES` - Max retries for executors (default: `5`)
   - `NWS_USER_AGENT_NAME` - NWS User-Agent name (default: `quantagent_capital`)
   - `NWS_USER_AGENT_EMAIL` - NWS User-Agent email (default: `jacob@quantagent_capital.ai`)
   - `WIND_SPEED_THRESHOLD_MPH` - Wind speed threshold for HWW validation (default: `65`)
   - `EVENT_CONFIRMATION_MAX_CONCURRENT` - Max concurrent event confirmations (default: `5`)

6. **Run the API server**:
   
   Make sure your virtual environment is activated (you should see `(venv)` in your terminal prompt).
   
   ```bash
   hypercorn main:app --reload
   ```
   
   The API will be available at `http://localhost:8000`
   
   You should see output indicating the server is starting. Wait a few seconds for it to fully initialize.

7. **Start the Celery worker** (for background tasks):
   
   In a separate terminal, with the virtual environment activated:
   
   ```bash
   celery -A app.celery_app worker --beat --loglevel=info
   ```
   
   This starts both the Celery worker and the CeleryBeat scheduler. Background tasks will run on their configured schedules:
   - **Disaster Polling Agent**: Every 15 minutes
   - **Event Confirmation Task**: Every hour
   - **Wildfire Sync Task**: Daily at 8:30 AM EST / 9:30 AM EDT (13:30 UTC)
   - **Drought Sync Task**: Manual trigger only (via API endpoint)
   - **ETL Task**: Every 6 hours (syncs confirmed, inactive, unprocessed events to ClickHouse)
   
   **Viewing Task Output:**
   - The task will log detailed output to the console with `INFO` level logging
   - To see even more detail, use `--loglevel=debug`:
     ```bash
     celery -A app.celery_app worker --beat --loglevel=debug
     ```
   - To manually trigger tasks for testing:
     ```bash
     celery -A app.celery_app call app.tasks.disaster_polling_task
     celery -A app.celery_app call app.tasks.events_confirmation_task
     celery -A app.celery_app call app.tasks.wildfire_sync_task
     celery -A app.celery_app call app.tasks.drought_sync_task
     celery -A app.celery_app call app.tasks.etl_task
     ```
   - To monitor task execution in real-time, use Flower (optional):
     ```bash
     pip install flower
     celery -A app.celery_app flower
     ```
     Then visit `http://localhost:5555` in your browser

   **Debugging in Cursor IDE:**
   - Open the Run and Debug panel (Cmd+Shift+D / Ctrl+Shift+D)
   - Select one of these debug configurations:
     - **Debug: Railway Local (Full Stack)** - Runs both Celery worker and FastAPI server (matches Railway exactly) ⭐ Recommended for production-like debugging
     - **Debug: Disaster Polling Task (Direct)** - Runs the task directly without Celery (best for debugging task logic)
     - **Debug: FastAPI Server** - Starts the FastAPI server with hot-reload
   - Set breakpoints in your code and press F5 to start debugging
   - You can also run debug scripts directly:
     ```bash
     python debug/railway_local.py     # Run full stack (Celery + FastAPI) ⭐ Recommended
     python debug/task_direct.py        # Run task directly (no Celery)
     python debug/test_setup.py         # Verify debug setup
     ```
   - See `debug/README.md` for detailed debugging instructions

8. **Access the API documentation**:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

### Health Check

Test the API and Redis connection:
```bash
curl http://localhost:8000/health
```

### Stopping Services

- **Stop the API**: Press `Ctrl+C` in the terminal running hypercorn
- **Stop Celery Worker**: Press `Ctrl+C` in the terminal running celery
- **Stop Redis**: `docker-compose down`
- **Stop Redis and remove data**: `docker-compose down -v`

## 📁 Project Structure

```
quantagentic_api/
├── app/
│   ├── __init__.py
│   ├── config.py                    # Configuration settings (Redis, Gemini, Celery)
│   ├── celery_app.py                # Celery application configuration
│   ├── redis_client.py              # Redis client wrapper (quantagent_redis)
│   ├── state.py                     # Shared state object for API and agents
│   ├── schemas/                     # Pydantic models (Event, Wildfire, Drought, Location)
│   ├── services/                    # Business logic layer (CRUD services, event services)
│   ├── controllers/                 # FastAPI route handlers (events, wildfires, droughts)
│   ├── processors/                  # Data processing logic (wildfire, event creation)
│   ├── http_client/                 # HTTP clients for external APIs
│   │   ├── nws_client.py            # NWS API client
│   │   ├── wildfire_client.py      # ArcGIS Wildfire API client
│   │   └── drought_client.py        # US Drought Monitor API client
│   ├── utils/                       # Utility functions
│   │   ├── arcgis_wildfire_parser.py  # ArcGIS wildfire data parser
│   │   ├── datetime_utils.py        # Datetime utilities
│   │   ├── event_types.py          # NWS event type codes
│   │   └── vtec.py                  # VTEC key generation
│   ├── agents/                      # CrewAI agents (single-agent tasks)
│   │   ├── wind_validation_agent.py  # Wind validation agent for HWW events
│   │   └── models.py                 # Agent output models
│   ├── crews/                       # CrewAI crews and shared resources
│   │   ├── base_executor.py         # Base executor with retry logic
│   │   ├── event_confirmation_crew/  # Event confirmation crew
│   │   │   ├── crew.py              # Crew definition
│   │   │   ├── executor.py          # Executor with retry logic
│   │   │   ├── models.py            # Structured Pydantic outputs
│   │   │   └── tools/               # Crew-specific tools
│   │   │       └── event_confirmation_tool.py
│   │   └── tools/                   # Shared CrewAI tools
│   ├── tasks/                       # Celery tasks
│   │   ├── disaster_polling_task.py  # NWS alert polling task
│   │   ├── events_confirmation_task.py  # Event confirmation task
│   │   ├── wildfire_sync_task.py      # Wildfire sync task
│   │   └── drought_sync_task.py       # Drought sync task
│   ├── pollers/                     # Polling tools
│   │   └── nws_polling_tool.py      # NWS polling tool
│   └── exceptions/                  # Custom exception classes
│       ├── base.py                  # Base exception classes
│       └── handler.py               # Exception handlers
├── debug/                           # Debug scripts for local testing
│   ├── railway_local.py            # Run full stack (Celery + FastAPI) ⭐ Recommended
│   ├── task_direct.py              # Run task directly (no Celery)
│   ├── test_setup.py               # Verify debug setup
│   └── README.md                   # Debugging guide
├── tests/                           # Unit and integration tests (see tests/README.md)
├── .vscode/                         # VS Code/Cursor IDE debug configurations
│   └── launch.json                 # Debug launch configurations
├── main.py                           # FastAPI application entry point
├── requirements.txt                  # Python dependencies
├── docker-compose.yml                # Redis Docker setup
├── pytest.ini                        # Pytest configuration
└── railway.json                      # Railway deployment config
```

## 🔌 API Endpoints

### Events (NWS Alerts)
- `GET /events` - List all events (supports `?active_only=true/false`)
- `GET /events/{event_key}` - Get event by key
- `GET /events/{event_key}/has_episode` - Check if event has an associated episode
- `GET /events/stats/counts-by-type` - Get count of active events grouped by event type
- `POST /events` - Create a new event from NWS alert
- `PUT /events/{event_key}` - Update event
- `POST /events/{event_key}/deactivate` - Deactivate an event (sets `is_active=False` and `actual_end_date` to now)
- `POST /events/confirm/{event_key}` - Confirm a specific event using LSR data
- `POST /events/confirm` - Confirm all active and unconfirmed events (runs asynchronously)
- `POST /events/etl` - Manually trigger ETL job to sync events to ClickHouse (runs asynchronously)

### Wildfires
- `GET /wildfire` - List all wildfires (supports `?active_only=true/false`)
- `GET /wildfire/{event_key}` - Get wildfire by event key
- `POST /wildfire/sync` - Manually trigger wildfire sync (runs asynchronously)

### Droughts
- `GET /drought` - List all drought events (supports `?active_only=true/false`)
- `GET /drought/{event_key}` - Get drought event by event key
- `POST /drought/sync` - Manually trigger drought sync (runs asynchronously)

## 🤖 Background Workers

### Disaster Polling Agent (NWS Alerts)

The disaster polling agent is a CrewAI-powered background worker that:

1. **Polls NWS API** every 15 minutes for active alerts
2. **Filters alerts** by severity, urgency, certainty, and event type
3. **Filters out FWW events** - Fire Weather Warnings are handled elsewhere
4. **Validates HWW events** - High Wind Warnings are validated using `WindValidationAgent` to ensure wind speed meets threshold (default 65 MPH)
5. **Creates VTEC keys** for unique identification
6. **Verifies keys** to ensure data quality
7. **Classifies alerts** into:
   - `new_events` - New warnings to create
   - `updated_events` - Existing warnings to update
8. **Manages event lifecycle** - Automatically completes events when alerts expire

**See**: `app/crews/disaster_polling_agent/README.md` for detailed documentation.

### Event Confirmation Task

The event confirmation task automatically confirms events using Local Storm Reports (LSRs):

1. **Fetches LSRs** from NWS API for each active and unconfirmed event
2. **Filters LSRs** using smart polling - only processes new LSRs (tracks polled LSR IDs)
3. **Uses CrewAI crew** to extract coordinates from LSR descriptions
4. **Validates coordinates** against event polygon boundaries
5. **Sets observed coordinates** on specific event locations based on confirmation results
6. **Processes all LSRs** - no short-circuit, allows multiple confirmations per event
7. **Marks LSRs as polled** only after successful processing (exceptions don't mark as polled)
8. **Sets observed coordinates** on specific event locations based on `location_index` from each confirmation

**Task**: `app.tasks.events_confirmation_task` (runs every hour via CeleryBeat schedule)

### Wildfire Sync Task

The wildfire sync task automatically:

1. **Polls ArcGIS API** for new and updated wildfires
2. **Tracks active wildfires** - Type 1, 2, and 3 incidents
3. **Manages wildfire lifecycle** using 3-tiered logic:
   - Not officially out (`attr_FireOutDateTime` is None)
   - Not 100% contained (`attr_PercentContained < 100`)
   - Data is fresh (modified within configured staleness threshold)
4. **Extracts comprehensive data**:
   - Location (coordinates, shapes, FIPS codes)
   - Severity (Type 1/2/3 incidents)
   - Acres burned, cost, containment percentage
   - Fuel sources and descriptions

**Task**: `app.tasks.wildfire_sync_task` (runs on CeleryBeat schedule)

### Drought Sync Task

The drought sync task automatically:

1. **Fetches current and previous week** drought monitor data
2. **Compares county-level drought conditions** using polygon intersections
3. **Creates drought events** when counties enter drought conditions
4. **Updates severity** when drought conditions worsen
5. **Completes drought events** when counties exit drought conditions
6. **Uses Tuesday date logic** - Accounts for data publication schedule (Thursdays)

**Task**: `app.tasks.drought_sync_task` (runs on CeleryBeat schedule)

### ETL Task (ClickHouse Sync)

The ETL task automatically syncs confirmed, inactive, unprocessed events to ClickHouse:

1. **Selects events** that meet all criteria:
   - `confirmed=True` - Event has been confirmed via LSR data
   - `is_active=False` - Event is no longer active
   - `etl_processed=False` - Event has not been processed by ETL yet
2. **Checks for idempotency** - Skips events that already exist in ClickHouse (prevents duplicates)
3. **Batch inserts** events and their locations to ClickHouse
4. **Marks events as processed** - Sets `etl_processed=True` after successful insertion
5. **Error handling** - Retries up to 3 times with exponential backoff on failure
6. **Comprehensive logging** - Logs all operations for monitoring and debugging

**When events are selected for ETL:**
- Events must be **confirmed** (have proof they occurred via LSR data)
- Events must be **inactive** (no longer active, typically after `actual_end_date` is set)
- Events must be **unprocessed** (`etl_processed=False`)

This ensures only completed, verified events are archived to ClickHouse for long-term storage and analysis.

**Task**: `app.tasks.etl_task` (runs every 6 hours via CeleryBeat schedule)

**ClickHouse Tables:**
- `disaster_events` - Main events table with all event metadata
- `disaster_locations` - Locations table with geographic data for each event

See `clickhouse_schema.sql` for table creation scripts.

## 🛠️ Development

### Running Tests

See `tests/README.md` for comprehensive testing documentation.

Quick start:
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_nws_polling_tool.py
```

### Code Style

This project uses snake_case naming conventions throughout.

**Note**: Celery broker and result backend automatically use the same Redis instance configured above.

## 📝 Notes

### Data Sources

- **NWS Alerts**: Real-time weather alerts from National Weather Service API
- **Wildfires**: ArcGIS API with ~36 hour delay (data from ~36 hours ago)
- **Droughts**: US Drought Monitor data published on Thursdays for previous Tuesday

### Technical Details

- Redis data persists in a Docker volume (`redis_data`)
- The API uses Pydantic models for request/response validation
- All NWS API calls include the required User-Agent header
- The shared state object (`app.state`) is accessible throughout the application
- CrewAI tasks use structured Pydantic outputs for better agent memory and consistency
- Wildfire data uses ArcGIS parser (`ArcGISWildfireParser`) for extracting and transforming feature data
- Drought data uses Tuesday date logic to account for publication schedule

## 🔗 Useful Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/tutorial/)
- [Hypercorn Documentation](https://hypercorn.readthedocs.io/)
- [Redis Documentation](https://redis.io/docs/)
- [CrewAI Documentation](https://docs.crewai.com/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Pytest Documentation](https://docs.pytest.org/)
