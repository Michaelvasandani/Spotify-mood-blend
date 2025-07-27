import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
import uvicorn

load_dotenv()

app = FastAPI(title="Spotify Mood Blend API")

from src.routes import auth, data

app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(data.router, prefix="/api", tags=["data"])

@app.get("/")
async def root():
    return {
        "message": "Spotify Mood Blend API",
        "endpoints": {
            "auth": "/auth/login",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)