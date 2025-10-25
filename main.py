# main.py
# NextBestAction API — FastAPI + MABWiser (cold-start safe) with real Bearer auth in Swagger
# Swagger URL: /docs  |  Health: GET /

from __future__ import annotations
import os, math, threading
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from joblib import dump, load

from mabwiser.mab import MAB, LearningPolicy, NeighborhoodPolicy

# -------------------------
# App & Security (Swagger "Authorize" will inject the header once you authorize)
# -------------------------
app = FastAPI(title="NextBestAction API", version="1.0.0")

bearer = HTTPBearer(auto_error=True)

def require_token(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> bool:
    if creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Use Bearer token")
    expected = os.environ.get("NBA_API_KEY", "dev")
    if creds.credentials != expected:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True

# -------------------------
# Config & In-Memory
# -------------------------
NBA_MODEL_PATH = os.environ.get("NBA_MODEL_PATH", "nba_model.joblib")
LOCK = threading.Lock()

ACTIONS_BY_STAGE: Dict[str, List[str]] = {
    "AWR": ["invite", "prep", "follow_up_t2", "discovery_invite"],
    "EDU": ["diagnose_spiced", "impact_calc", "case_study_send"],
    "SEL": ["meddic_gap_check", "stakeholder_map", "pilot_roi_calc", "exec_sponsor_outreach", "legal_prep"],
    "MUTCOM": ["pilot_sow_review", "security_review", "data_mapping_check"],
    "ONB": ["connector_setup", "first_value_event", "risk_triage"],
    "RECIMPACT": ["habit_coach", "qbr_schedule", "health_review"],
    "EXP": ["eligibility_list", "expansion_proposal", "referral_ask"],
    "ADV": ["case_brief", "webinar_invite", "reference_call"],
}

def _new_model(arms: List[str]) -> MAB:
    return MAB(
        arms=arms,
        learning_policy=LearningPolicy.LinUCB(alpha=0.3),
        neighborhood_policy=NeighborhoodPolicy.KNN(k=0)  # off
    )

def _load_or_init(arms: List[str]) -> MAB:
    if os.path.exists(NBA_MODEL_PATH):
        try:
            m: MAB = load(NBA_MODEL_PATH)
            # if arms changed since last run, reinit cleanly
            if set(getattr(m, "arms", [])) != set(arms):
                m = _new_model(arms)
            return m
        except Exception:
            # corrupted file or incompatible version — start fresh
            return _new_model(arms)
    return _new_model(arms)

def _vectorize(features: Dict[str, Any]) -> List[float]:
    # Simple, deterministic featurizer:
    # - numeric/bool -> float
    # - everything else -> stable [0,1) hash bucket
    vec: List[float] = []
    for k in sorted(features.keys()):
        v = features[k]
        if isinstance(v, (int, float)):
            vec.append(float(v))
        elif isinstance(v, bool):
            vec.append(1.0 if v else 0.0)
        else:
            vec.append((abs(hash(str(v))) % 1000) / 1000.0)
    return vec

# -------------------------
# Schemas
# -------------------------
class NBARequest(BaseModel):
    run_id: str
    account_id: str
    stage: str
    allowed_actions: List[str]
    k: int = 3
    features: Dict[str, Any]
    goal: str | None = None
    debug: bool = False

class Feedback(BaseModel):
    run_id: str
    account_id: str
    stage: str
    action: str
    reward: float  # 1.0 if stage exited within SLA; 0.0 if not (you can shape this later)
    context: Dict[str, Any]

# -------------------------
# Routes
# -------------------------
@app.get("/")
def health():
    return {"ok": True, "service": "NextBestAction API"}

@app.post("/next_best_action")
def next_best_action(payload: NBARequest, _: bool = Depends(require_token)):
    stage = (payload.stage or "").upper()
    default_arms = ACTIONS_BY_STAGE.get(stage, [])
    # enforce fences against the stage’s allowed list
    arms = [a for a in payload.allowed_actions if a in default_arms] or default_arms
    if not arms:
        raise HTTPException(status_code=400, detail=f"No configured actions for stage {stage}")

    x = _vectorize(payload.features)

    with LOCK:
        mab = _load_or_init(arms)
        # Try scoring expectations per arm; be cold-start safe
        scores: Dict[str, float] = {a: 0.0 for a in arms}
        try:
            if hasattr(mab, "predict_expectations"):
                pe = mab.predict_expectations(context=x)  # returns dict arm->score
                for a in arms:
                    scores[a] = float(pe.get(a, 0.0))
            else:
                # Older MABWiser versions
                for a in arms:
                    try:
                        scores[a] = float(mab.predict_expectation(context=x, arm=a))
                    except Exception:
                        scores[a] = 0.0
        except Exception:
            # still return a valid list on day 0
            scores = {a: 0.0 for a in arms}

        # Simple exploration bonus that works even before any training
        n = getattr(mab, "n", {}) if hasattr(mab, "n") else {}
        ranked = sorted(
            arms,
            key=lambda a: scores.get(a, 0.0) + 0.3 / ((n.get(a, 0) + 1) ** 0.5),
            reverse=True
        )
        topk = ranked[: max(1, payload.k)]

        # persist model (even untrained) to keep state on disk between requests
        dump(mab, NBA_MODEL_PATH)

    choices = [{
        "action": a,
        "score": float(scores.get(a, 0.0)),
        "uncertainty": round(0.3 / ((n.get(a, 0) + 1) ** 0.5), 3),
        "expected": {"cr_uplift": 0.01, "delta_t_days": -0.5}  # illustrative; replace with your own estimates
    } for a in topk]

    return {"choices": choices, "policy": "mabwiser.linucb", "notes": "cold-start safe; send /feedback to learn"}

@app.post("/feedback")
def feedback(fb: Feedback, _: bool = Depends(require_token)):
    # Update the bandit online from a single example
    stage = (fb.stage or "").upper()
    arms = ACTIONS_BY_STAGE.get(stage, [])
    if fb.action not in arms:
        arms.append(fb.action)

    x = _vectorize(fb.context)

    with LOCK:
        mab = _load_or_init(arms)
        try:
            # Most recent MABWiser has partial_fit; fit on single sample also works
            if hasattr(mab, "partial_fit"):
                mab.partial_fit(decisions=[fb.action], rewards=[fb.reward], contexts=[x])
            else:
                mab.fit(decisions=[fb.action], rewards=[fb.reward], contexts=[x])
        except Exception:
            # If anything odd happens, start fresh and fit once
            mab = _new_model(arms)
            mab.fit(decisions=[fb.action], rewards=[fb.reward], contexts=[x])
        dump(mab, NBA_MODEL_PATH)

    return {"ok": True}
