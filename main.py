from fastapi import FastAPI, Body
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import re

app = FastAPI(title="Hedge Fund – ClearLine Bridge")

# --- helpers ---------------------------------------------------------------
def _split_csv(name: str, default: str = "") -> List[str]:
    raw = os.getenv(name, default)
    return [x.strip().upper() for x in raw.split(",") if x.strip()]

WATCHLIST = set(
    _split_csv("WATCHLIST_1")
    + _split_csv("WATCHLIST_2")
    + _split_csv("WATCHLIST_3")
)

POS_KEYWORDS = [k for k in _split_csv("POSITIVE_KEYWORDS", "upgrade,beat,record,win,profit,raise")]
NEG_KEYWORDS = [k for k in _split_csv("NEGATIVE_KEYWORDS", "downgrade,miss,loss,cut,probe,recall")]

ALERT_TO = os.getenv("ALERT_TO", "").strip()
SUBJECT_PREFIX = os.getenv("SUBJECT_PREFIX", "Revolut Tips \"A\"").strip()

def score_text(text: str) -> int:
    """Nagyon egyszerű szöveg-szignál: +1 / találat, -1 / negatív találat"""
    if not text:
        return 0
    t = text.upper()
    p = sum(1 for k in POS_KEYWORDS if re.search(rf"\b{re.escape(k)}\b", t))
    n = sum(1 for k in NEG_KEYWORDS if re.search(rf"\b{re.escape(k)}\b", t))
    return p - n

def classify(symbol: str, title: str, summary: str, base_sentiment: Optional[float]) -> str:
    s = (base_sentiment or 0.0) + score_text(title) + 0.5 * score_text(summary)
    # egyszerű küszöbök
    if s >= 2 and symbol in WATCHLIST:
        return "A"
    if s >= 1:
        return "B"
    return "C"

# --- models ----------------------------------------------------------------
class IngestItem(BaseModel):
    source: str = Field(..., example="marketaux")
    symbol: str = Field(..., example="AAPL")
    title: str = Field(..., example="Apple raises guidance on strong iPhone sales")
    url: Optional[str] = Field(None, example="https://news.example/item")
    summary: Optional[str] = Field(None, example="Short description...")
    sentiment: Optional[float] = Field(None, description="-1..+1 (ha jön külső API-ból)")
    tags: Optional[List[str]] = None

class BridgeResponse(BaseModel):
    grade: str
    email_subject: str
    email_body: str
    accepted: bool
    reason: Optional[str] = None

# --- routes ----------------------------------------------------------------
@app.get("/health")
def health():
    return {"ok": True}

@app.post("/v1/clearline/bridge", response_model=BridgeResponse)
def clearline_bridge(item: IngestItem = Body(...)):
    sym = item.symbol.upper().strip()

    if not sym:
        return BridgeResponse(
            grade="C",
            email_subject="",
            email_body="",
            accepted=False,
            reason="Missing symbol",
        )

    grade = classify(sym, item.title or "", item.summary or "", item.sentiment)

    subject = f'{SUBJECT_PREFIX}: {sym} → {grade}'
    body_lines = [
        f"Source: {item.source}",
        f"Symbol: {sym}",
        f"Grade: {grade}",
        f"Title: {item.title or '-'}",
        f"URL: {item.url or '-'}",
        f"Sentiment(base): {item.sentiment}",
        f"Tags: {', '.join(item.tags or []) or '-'}",
    ]
    if item.summary:
        body_lines.append("")
        body_lines.append("Summary:")
        body_lines.append(item.summary)

    body = "\n".join(body_lines)

    # Itt most csak VISSZAADJUK a riasztás tartalmát.
    # (Ha készen állsz az e-mail küldésre, a Mailgun/Mailjet hívást ide tesszük,
    #  és az MX_KEY-ből az API kulcsot olvassuk. Most nem küldünk levelet.)
    return BridgeResponse(
        grade=grade,
        email_subject=subject,
        email_body=body,
        accepted=True,
        reason=None,
    )

# root – kompatibilitás
@app.get("/")
def root():
    return {"greeting": "Hello, World!", "message": "Hedge Fund backend is live."}
@app.get("/")
def root():
    return {"greeting": "Hello, World!", "message": "Hedge Fund backend is live."}

@app.get("/clearline-bridge")
def clearline_bridge():
    return {
        "status": "active",
        "module": "ClearLine Bridge",
        "message": "Connection established successfully."
    }
