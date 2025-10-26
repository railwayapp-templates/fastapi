from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"greeting": "Hello, World", "message": "Welcome to EMMA’s model service!"}

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/version")
def version():
    return {"version": "v1.0.0"}

@app.post("/projection_1yr")
def projection_1yr():
    return {"ok": True, "endpoint": "projection_1yr", "message": "Placeholder working."}

@app.post("/projection_3yr")
def projection_3yr():
    return {"ok": True, "endpoint": "projection_3yr", "message": "Placeholder working."}

@app.post("/projection_5yr")
def projection_5yr():
    return {"ok": True, "endpoint": "projection_5yr", "message": "Placeholder working."}

@app.post("/sensitivity")
def sensitivity():
    return {"ok": True, "endpoint": "sensitivity", "message": "Placeholder working."}

@app.post("/timeline_check")
def timeline_check():
    return {"ok": True, "endpoint": "timeline_check", "message": "Placeholder working."}
