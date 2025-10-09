from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import Optional
import os
import re

app = FastAPI(title="Hedge Fund – ClearLine Bridge")

# --- helpers ----------------------------
def _split_csv(name: str, default: str = ""):
    raw = os.getenv(name, default)
    return [x.strip().upper() for x in raw.split(",") if x.strip()]

# --- core data ---------------------------
WATCHLIST = set(
    _split_csv("WATCHLIST_1")
    + _split_csv("WATCHLIST_2")
    + _split_csv("WATCHLIST_3")
)
POS_KEYWORDS = [k for k in _split_csv("POS_KEYWORDS")]
NEG_KEYWORDS = [k for k in _split_csv("NEG_KEYWORDS")]

ALERT_TO = os.getenv("ALERT_TO", "").strip()
SUBJECT_PREFIX = os.getenv("SUBJECT_PREFIX", "[CLEARLINE]")

# --- models ------------------------------
class TextPayload(BaseModel):
    text: str
    source: Optional[str] = "Unknown"

# --- scoring logic -----------------------
def score_text(text: str) -> int:
    text_up = text.upper()
    score = 0
    for pos in POS_KEYWORDS:
        if pos in text_up:
            score += 1
    for neg in NEG_KEYWORDS:
        if neg in text_up:
            score -= 1
    return score

# --- endpoints ---------------------------
@app.get("/")
def root():
    return {"status": "running", "message": "ClearLine Bridge active"}

@app.post("/clearline")
def analyze_text(payload: TextPayload = Body(...)):
    s = score_text(payload.text)
    return {
        "source": payload.source,
        "score": s,
        "decision": "POSITIVE" if s > 0 else "NEGATIVE" if s < 0 else "NEUTRAL"
    }

@app.get("/clearline-bridge")
def clearline_status():
    return {
        "status": "online",
        "system": "ClearLine API",
        "message": "Bridge active and ready"
    }
