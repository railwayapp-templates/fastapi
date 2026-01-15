import os
from typing import Optional
from crewai import LLM
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
	# Redis configuration
	redis_host: str = os.getenv("REDIS_HOST", "localhost")
	redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
	redis_db: int = int(os.getenv("REDIS_DB", "0"))
	redis_password: Optional[str] = os.getenv("REDIS_PASSWORD", None)
	
	# NWS API configuration
	nws_user_agent_name: str = os.getenv("NWS_USER_AGENT_NAME", "quantagent_capital")
	nws_user_agent_email: str = os.getenv("NWS_USER_AGENT_EMAIL", "jacob@quantagent_capital.ai")
	
	# CrewAI / Gemini configuration
	gemini_model: str = os.getenv("GEMINI_MODEL", "gemini/gemini-3-pro-preview")
	gemini_api_key: str = os.getenv("GEMINI_API_KEY", "test")
	
	# Celery configuration
	executor_max_retries: int = int(os.getenv("EXECUTOR_MAX_RETRIES", "5"))
	
	# QuantAgentic API configuration
	quantagentic_api_base_url: str = os.getenv("QUANTAGENTIC_API_BASE_URL", "http://localhost")
	quantagent_api_port: int = int(os.getenv("QUANTAGENT_API_PORT", "8000"))

	ugc_zone_base_url: str = os.getenv("UGC_ZONE_BASE_URL", "https://api.weather.gov/zones/county/")
	
	# Event completion checking configuration
	event_completion_timeout_minutes: int = int(os.getenv("EVENT_COMPLETION_TIMEOUT_MINUTES", "20"))
	
	# NWS polling filter configuration
	nws_polling_certainty: str = os.getenv("NWS_POLLING_CERTAINTY", "Observed,Likely")

	most_recent_drought_information_full_url: str = os.getenv("MOST_RECENT_DROUGHT_INFORMATION_FULL_URL", "https://www.ncei.noaa.gov/pub/data/nidis/geojson/us/usdm/USDM-current.geojson")
	last_weeks_drought_information_base_url: str = os.getenv("LAST_WEEKS_DROUGHT_INFORMATION_BASE_URL", "https://droughtmonitor.unl.edu/")

	# We care about 2, 3, and 4
	drought_severity_low_threshold: int = int(os.getenv("DROUGHT_SEVERITY_LOW_THRESHOLD", 2))
	drought_severity_high_threshold: int = int(os.getenv("DROUGHT_SEVERITY_HIGH_THRESHOLD", 4))


	# Wildfire staleness threshold (default: 7 days in milliseconds)
	wildfire_staleness_threshold_days: int = int(os.getenv("WILDFIRE_STALENESS_THRESHOLD_DAYS", 7))
	wildfire_staleness_threshold_ms: int = int(os.getenv("WILDFIRE_STALENESS_THRESHOLD_MS", str(wildfire_staleness_threshold_days * 24 * 60 * 60 * 1000)))
	
	# Wildfire ArcGIS API configuration
	wildfire_arcgis_base_url: str = os.getenv("WILDFIRE_ARCGIS_BASE_URL", "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/WFIGS_Interagency_Perimeters/FeatureServer/0/query")
	
	# Event confirmation parallel processing configuration
	event_confirmation_max_concurrent: int = int(os.getenv("EVENT_CONFIRMATION_MAX_CONCURRENT", "5"))
	
	# Wind validation configuration
	wind_speed_threshold_mph: int = int(os.getenv("WIND_SPEED_THRESHOLD_MPH", "65"))
	
	# ClickHouse configuration
	clickhouse_host: str = os.getenv("CH_HOST", "localhost")
	clickhouse_port: int = int(os.getenv("CH_PORT", "8123"))
	clickhouse_user: str = os.getenv("CH_USER", "default")
	clickhouse_password: str = os.getenv("CH_PASSWORD", "")
	clickhouse_connect_timeout: int = int(os.getenv("CH_CONNECT_TIMEOUT", "30"))  # Default: 30 seconds
	clickhouse_send_receive_timeout: int = int(os.getenv("CH_SEND_RECEIVE_TIMEOUT", "1200"))  # Default: 10 minutes
	
	@property
	def clickhouse_db(self) -> str:
		"""ClickHouse database name, with _dev suffix if IS_PR_ENV is true."""
		base_db = os.getenv("CH_DB", "default")
		is_pr_env = os.getenv("IS_PR_ENV", "false").lower() == "true"
		if is_pr_env:
			return f"{base_db}_dev"
		return base_db

	@property
	def default_llm(self) -> LLM:
		return LLM(
			model=self.gemini_model,
			api_key=self.gemini_api_key
		)

	@property           
	def quantagentic_api_url(self) -> str:
		"""Full QuantAgentic API URL."""
		return f"{self.quantagentic_api_base_url}:{self.quantagent_api_port}"
	
	@property
	def celery_broker_url(self) -> str:
		"""Celery broker URL - uses same Redis as application."""
		return self.redis_url
	
	@property
	def celery_result_backend(self) -> str:
		"""Celery result backend - uses same Redis as application."""
		return self.redis_url
	
	@property
	def redis_url(self) -> str:
		if self.redis_password:
			return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
		return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
	
	@property
	def nws_user_agent(self) -> str:
		"""Format NWS User-Agent header as required by NWS API."""
		return f"( {self.nws_user_agent_name}, {self.nws_user_agent_email} )"

settings = Settings()

