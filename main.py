from fastapi import FastAPI, HTTPException, Request
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from datetime import datetime
import httpx
import logging
import os
from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5173",
    "https://react-frontend-production-81f7.up.railway.app"
]


# Configuration management
class Settings(BaseSettings):
    # Add your API keys or other configuration here
    LOG_LEVEL: str = "INFO"
    PORT: int = int(os.getenv("PORT", "8080"))  # Cloud providers often specify port via PORT env var
    
    model_config = ConfigDict(env_file=".env")

settings = Settings()

# Setup logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Monitor")

# Add CORSMiddleware to the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler = AsyncIOScheduler(jobstores={'default': MemoryJobStore()})

class MonitoringConfig:
    is_active = False
    endpoint = None
    interval = None
    job = None

monitor_config = MonitoringConfig()

async def monitor_api():
    """Async function to check the API endpoint and log the response"""
    if not monitor_config.endpoint:
        logger.error("No endpoint configured for monitoring")
        return
    
    try:
        async with httpx.AsyncClient() as client:
            start_time = datetime.now()
            response = await client.get(monitor_config.endpoint)
            duration = (datetime.now() - start_time).total_seconds()
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "status_code": response.status_code,
                "response_time": f"{duration:.2f}s",
                "response_size": len(response.content),
                "endpoint": monitor_config.endpoint
            }
            
            logger.info(f"API Check Result: {log_entry}")
            
            # Cloud logging-friendly format
            print(log_entry)  # Cloud platforms can capture stdout
            
            if response.status_code >= 400:
                logger.error(f"API error: {response.text}")
                
    except Exception as e:
        error_msg = f"Monitoring failed: {str(e)}"
        logger.error(error_msg)
        print({"error": error_msg, "timestamp": datetime.now().isoformat()})

@app.post("/monitor/start")
async def start_monitoring(endpoint: str, interval_seconds: int = 60):
    """Start monitoring the specified API endpoint"""
    if monitor_config.is_active:
        raise HTTPException(status_code=400, detail="Monitoring is already active")
    
    monitor_config.endpoint = endpoint
    monitor_config.interval = interval_seconds
    monitor_config.is_active = True
    
    monitor_config.job = scheduler.add_job(
        monitor_api,
        'interval',
        seconds=interval_seconds,
        id='api_monitor',
        replace_existing=True
    )
    
    return {"status": "Monitoring started", "endpoint": endpoint, "interval": interval_seconds}

@app.post("/monitor/stop")
async def stop_monitoring():
    """Stop the current monitoring job"""
    if not monitor_config.is_active:
        raise HTTPException(status_code=400, detail="No active monitoring")
    
    if monitor_config.job:
        monitor_config.job.remove()
        monitor_config.job = None
    
    monitor_config.is_active = False
    monitor_config.endpoint = None
    monitor_config.interval = None
    
    return {"status": "Monitoring stopped"}

@app.get("/monitor/status")
async def get_status():
    """Get the current monitoring status"""
    return {
        "is_active": monitor_config.is_active,
        "endpoint": monitor_config.endpoint,
        "interval": monitor_config.interval
    }

# Health check endpoint (required by many cloud platforms)
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/callback")
async def handle_callback(request: Request):
    """Handle incoming callbacks from outside"""
    
    payload = await request.json()
    logger.info(f"Received callback: {datetime.now()} with payload: {payload}")
    
    return {"status": "Callback received"}

@app.on_event("startup")
async def startup_event():
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    if monitor_config.job:
        monitor_config.job.remove()
    scheduler.shutdown()