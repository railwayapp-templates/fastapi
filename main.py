# main.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

@app.get("/")
def root():
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}

@app.get("/healthz")
def healthz():
    return {"ok": True}

class SearchIn(BaseModel):
    username: str
    password: str
    q: str
    limit: int | None = 20

@app.post("/courses/search")
def courses_search(p: SearchIn):
    q = (p.q or "").strip()
    if len(q) < 2:
        return {"ok": True, "items": []}
    return {
        "ok": True,
        "items": [
            {"pp":"12345","lv":"67890","title":f"Beispielkurs {q.upper()}","lecturers":["Max Muster"],"free":3}
        ],
    }
