from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os

app = FastAPI()

# MCP API URL и ключ API (храните ключ безопасно)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")  # Убедитесь, что ключ добавлен в переменные окружения.
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/complete"

if not ANTHROPIC_API_KEY:
    raise ValueError("API ключ не найден! Убедитесь, что ANTHROPIC_API_KEY установлен.")

# Модель запроса
class ClaudeRequest(BaseModel):
    prompt: str
    max_tokens: int = 300
    temperature: float = 1.0
    stop_sequences: list = []

# Модель ответа
class ClaudeResponse(BaseModel):
    completion: str

# Эндпоинт для отправки запросов в Anthropic Claude
@app.post("/claude/completion", response_model=ClaudeResponse)
async def interact_with_claude(request: ClaudeRequest):
    headers = {
        "Authorization": f"Bearer {ANTHROPIC_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "prompt": request.prompt,
        "max_tokens_to_sample": request.max_tokens,
        "temperature": request.temperature,
        "stop_sequences": request.stop_sequences,
    }

    try:
        response = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return ClaudeResponse(completion=data.get("completion", ""))
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Ошибка запроса: {str(e)}")