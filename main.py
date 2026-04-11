from datetime import datetime, timezone
import os

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

from .db import insert_events, to_insert_row
from .models import AnalyticsBatchRequest, AnalyticsBatchResponse, RejectedEvent


app = FastAPI(title="Quiz Analytics API", version="1.0.0")
EXPECTED_API_KEY = os.getenv("ANALYTICS_API_KEY", "").strip()


@app.post("/analytics/events:ingest", response_model=AnalyticsBatchResponse)
async def ingest_events(
    batch: AnalyticsBatchRequest,
    x_analytics_api_key: str | None = Header(default=None),
):
    if EXPECTED_API_KEY and x_analytics_api_key != EXPECTED_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid analytics API key.")

    received_at_utc = datetime.now(timezone.utc)
    rows = []
    rejected = []

    for index, event in enumerate(batch.events):
        try:
            rows.append(to_insert_row(event.model_dump(mode="json"), received_at_utc))
        except Exception as exc:  # pragma: no cover - defensive fallback
            rejected.append(RejectedEvent(index=index, reason=str(exc)))

    inserted_count = insert_events(rows)
    response = AnalyticsBatchResponse(
        accepted_count=inserted_count,
        rejected_count=len(rejected),
        server_time_utc=received_at_utc,
        rejected=rejected,
    )
    return JSONResponse(content=response.model_dump(mode="json"))


@app.get("/healthz")
async def healthcheck():
    return {"status": "ok"}
