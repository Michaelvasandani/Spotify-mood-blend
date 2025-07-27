from fastapi import APIRouter, Query, HTTPException, Response, Request
from fastapi.responses import RedirectResponse
from typing import Optional
import secrets
import json
from datetime import datetime, timedelta

from ..utils.spotify_client import SpotifyClient

router = APIRouter()

sessions = {}

@router.get("/login")
async def login(response: Response):
    state = secrets.token_urlsafe(16)
    sessions[state] = {
        "created_at": datetime.now().isoformat()
    }
    
    spotify_client = SpotifyClient()
    auth_url = spotify_client.get_auth_url(state=state)
    
    return RedirectResponse(url=auth_url)

@router.get("/callback")
async def callback(
    request: Request,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None)
):
    if error:
        raise HTTPException(status_code=400, detail=f"Spotify authorization error: {error}")
    
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state parameter")
    
    if state not in sessions:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    try:
        spotify_client = SpotifyClient()
        token_info = spotify_client.get_access_token(code)
        
        sessions[state]["token_info"] = token_info
        sessions[state]["authenticated"] = True
        
        return {
            "status": "success",
            "message": "Successfully authenticated with Spotify",
            "access_token": token_info["access_token"],
            "expires_in": token_info["expires_in"],
            "refresh_token": token_info["refresh_token"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get access token: {str(e)}")

@router.post("/refresh")
async def refresh_token(refresh_token: str):
    try:
        spotify_client = SpotifyClient()
        new_token_info = spotify_client.refresh_access_token(refresh_token)
        
        return {
            "access_token": new_token_info["access_token"],
            "expires_in": new_token_info["expires_in"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to refresh token: {str(e)}")