from fastapi import FastAPI, BackgroundTasks
from app.tasks import send_email_task   

app = FastAPI()

@app.get("/")
async def root():
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}
@app.post("/send-email/")
async def send_email(email: str):
    send_email_task.delay(email)
    return {"status": "Email scheduled!"}