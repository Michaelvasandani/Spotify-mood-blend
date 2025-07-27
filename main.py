import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
import uvicorn

load_dotenv()

app = FastAPI(title="Spotify Mood Blend API")

from src.routes import auth, data, lyrics

app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(data.router, prefix="/api", tags=["data"])
app.include_router(lyrics.router, prefix="/api", tags=["lyrics"])

@app.get("/")
async def root():
    return {
        "message": "Spotify Mood Blend API",
        "endpoints": {
            "auth": "/auth/login",
            "top_tracks": "/api/top-tracks",
            "recently_played": "/api/recently-played",
            "lyrics": "/api/lyrics/{track_id}",
            "batch_lyrics": "/api/lyrics/batch",
            "cache_stats": "/api/lyrics/cache/stats",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)