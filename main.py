from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3

app = FastAPI()

# Connect to SQLite (you can switch to PostgreSQL in production)
conn = sqlite3.connect("memory.db")
cursor = conn.cursor()

# Create a table for storing memories
cursor.execute('''
    CREATE TABLE IF NOT EXISTS memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_input TEXT,
        response TEXT
    )
''')
conn.commit()

# Define a data model
class MemoryEntry(BaseModel):
    user_input: str
    response: str

# Store memory endpoint
@app.post("/store_memory/")
def store_memory(entry: MemoryEntry):
    cursor.execute("INSERT INTO memory (user_input, response) VALUES (?, ?)", 
                   (entry.user_input, entry.response))
    conn.commit()
    return {"message": "Memory stored successfully"}

# Retrieve stored memories
@app.get("/retrieve_memory/")
def retrieve_memory():
    cursor.execute("SELECT * FROM memory ORDER BY id DESC LIMIT 5")
    data = cursor.fetchall()
    return {"memories": data}

# Root endpoint (to confirm API is running)
@app.get("/")
def root():
    return {"message": "Nikita Prime Memory System is running!"}
