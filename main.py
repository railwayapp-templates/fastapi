from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import json
from anthropic import Anthropic
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Life Path Guidance API", version="1.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Claude
claude = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Models
class StoryInput(BaseModel):
    content: str
    analysis_type: Optional[str] = "archetypes"

class AnalysisResponse(BaseModel):
    status: str
    data: Dict[str, Any]
    message: Optional[str] = None

# Routes
@app.get("/")
def home():
    return {
        "service": "Life Path Guidance API",
        "status": "running",
        "version": "1.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "analyze_story": "/api/v1/analyze"
        }
    }

@app.get("/health")
def health():
    return {"status": "healthy", "claude_api": bool(os.getenv("ANTHROPIC_API_KEY"))}

@app.get("/test-claude")
def test_claude():
    """Test Claude API connection"""
    if not os.getenv("ANTHROPIC_API_KEY"):
        return {"error": "Claude API key not set in environment variables"}
    
    try:
        response = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": "Reply with only: 'Claude API is working correctly'"
            }]
        )
        return {
            "status": "success",
            "claude_response": response.content[0].text,
            "model": "claude-sonnet-4-20250514"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/api/v1/analyze", response_model=AnalysisResponse)
async def analyze_story(story: StoryInput):
    """Analyze a life story using Claude"""
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=500, detail="Claude API key not configured")
    
    if len(story.content) < 50:
        raise HTTPException(status_code=400, detail="Story too short. Minimum 50 characters.")
    
    # Build prompt based on analysis type
    if story.analysis_type == "archetypes":
        prompt = f"""Analyze this life story and identify dominant archetypes:

{story.content}

Return ONLY valid JSON with this structure:
{{
  "archetypes": [
    {{
      "name": "Archetype Name",
      "confidence": 85,
      "evidence": ["Specific evidence from story"],
      "description": "How this archetype manifests"
    }}
  ],
  "summary": "Brief summary of their archetypal patterns"
}}"""
    else:
        prompt = f"""Analyze this life story:

{story.content}

Return ONLY valid JSON with insights about the person."""
    
    try:
        # Call Claude
        response = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Extract JSON from response
        response_text = response.content[0].text
        
        # Handle markdown code blocks
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            json_str = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            json_str = response_text[start:end].strip()
        else:
            json_str = response_text.strip()
        
        # Parse JSON
        analysis_data = json.loads(json_str)
        
        return AnalysisResponse(
            status="success",
            data=analysis_data,
            message=f"Analysis complete. Tokens used: {response.usage.input_tokens + response.usage.output_tokens}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Claude analysis failed: {str(e)}")

# For Railway
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
