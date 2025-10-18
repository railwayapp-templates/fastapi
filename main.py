import os
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, conlist
from typing import List
from sentence_transformers import SentenceTransformer
import uvicorn

API_KEY = os.getenv("EMBED_API_KEY", "")
MODEL_ID = os.getenv("EMBED_MODEL", "BAAI/bge-small-en")
PORT = int(os.getenv("PORT", "8080"))

app = FastAPI(title="Embedding Service", version="1.0.0")

# Load model once at startup (auto-downloads from Hugging Face if not baked in)
model = SentenceTransformer(MODEL_ID)
# bge recommends L2-normalized embeddings for cosine similarity
def encode(texts: List[str]) -> List[List[float]]:
    embs = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    return [e.tolist() for e in embs]

def auth(request: Request):
    if not API_KEY:
        return  # no auth configured
    header = request.headers.get("authorization") or ""
    if not header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing/invalid auth")
    token = header.split(" ", 1)[1].strip()
    if token != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

class EmbedIn(BaseModel):
    text: str

class BatchEmbedIn(BaseModel):
    texts: List[str]

class EmbedOut(BaseModel):
    embedding: conlist(float, min_items=1)

class BatchEmbedOut(BaseModel):
    embeddings: List[conlist(float, min_items=1)]

@app.get("/health")
def health():
    # If model loaded, we're ready
    dim = len(encode(["ok"])[0])
    return {"status": "ready", "model": MODEL_ID, "dim": dim}

@app.post("/embed", response_model=EmbedOut)
async def embed(req: Request, body: EmbedIn):
    auth(req)
    vec = encode([body.text])[0]
    return {"embedding": vec}

@app.post("/batch_embed", response_model=BatchEmbedOut)
async def batch_embed(req: Request, body: BatchEmbedIn):
    auth(req)
    if not body.texts:
        raise HTTPException(400, "texts cannot be empty")
    # Good default batch size for CPU; adjust later if needed
    embeddings = []
    step = 64
    for i in range(0, len(body.texts), step):
        embeddings.extend(encode(body.texts[i:i+step]))
    return {"embeddings": embeddings}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, workers=1)
