from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import spotipy

from ..models.database import get_db, init_db
from ..models.lyrics_models import (
    LyricsResponse, 
    BatchLyricsRequest, 
    CacheStatsResponse,
    GeniusSearchResponse
)
from ..utils.lyrics_cache import LyricsCache
from ..utils.spotify_client import SpotifyClient

router = APIRouter()

# Initialize database on startup
init_db()

lyrics_cache = LyricsCache()

def get_spotify_client_from_token(token: str) -> spotipy.Spotify:
    spotify_client = SpotifyClient()
    return spotify_client.get_spotify_client(token)

@router.get("/lyrics/{track_id}", response_model=LyricsResponse)
async def get_lyrics_for_track(
    track_id: str,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """Get lyrics for a specific Spotify track ID"""
    try:
        # Get track info from Spotify first
        token = authorization.replace("Bearer ", "")
        sp = get_spotify_client_from_token(token)
        
        track_info = sp.track(track_id)
        if not track_info:
            raise HTTPException(status_code=404, detail="Track not found on Spotify")
        
        artist = track_info['artists'][0]['name'] if track_info['artists'] else "Unknown"
        title = track_info['name']
        
        # Fetch lyrics
        result = lyrics_cache.fetch_and_cache_lyrics(db, track_id, artist, title)
        
        return LyricsResponse(
            spotify_track_id=track_id,
            artist=artist,
            title=title,
            lyrics=result.get("lyrics"),
            genius_url=result.get("genius_url"),
            source=result.get("source", "unknown"),
            cached_at=result.get("cached_at", ""),
            cache_id=result.get("cache_id", 0),
            error=result.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch lyrics: {str(e)}")

@router.post("/lyrics/batch", response_model=List[LyricsResponse])
async def get_batch_lyrics(
    request: BatchLyricsRequest,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """Get lyrics for multiple tracks"""
    try:
        # Validate tracks have required fields
        for track in request.tracks:
            if not all(key in track for key in ['id', 'name', 'artists']):
                raise HTTPException(
                    status_code=400, 
                    detail="Each track must have 'id', 'name', and 'artists' fields"
                )
        
        # Process batch
        results = lyrics_cache.batch_fetch_lyrics(db, request.tracks)
        
        # Convert to response models
        responses = []
        for result in results:
            responses.append(LyricsResponse(
                spotify_track_id=result.get("spotify_track_id", ""),
                artist=result.get("artist", ""),
                title=result.get("title", ""),
                lyrics=result.get("lyrics"),
                genius_url=result.get("genius_url"),
                source=result.get("source", "unknown"),
                cached_at=result.get("cached_at", ""),
                cache_id=result.get("cache_id", 0),
                error=result.get("error")
            ))
        
        return responses
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch batch lyrics: {str(e)}")

@router.get("/lyrics/search/{artist}/{title}", response_model=GeniusSearchResponse)
async def search_genius(
    artist: str,
    title: str,
    db: Session = Depends(get_db)
):
    """Search for a song on Genius without caching"""
    try:
        result = lyrics_cache.genius_client.search_song(artist, title)
        
        if not result:
            return GeniusSearchResponse(
                genius_id=None,
                genius_title=None,
                genius_artist=None,
                genius_url=None,
                match_score=0,
                confidence="none"
            )
        
        # Calculate match score using fuzzy matching
        scores = lyrics_cache.fuzzy_matcher.match_artist_title(
            artist, title, result["artist"], result["title"]
        )
        
        return GeniusSearchResponse(
            genius_id=str(result["id"]),
            genius_title=result["title"],
            genius_artist=result["artist"],
            genius_url=result["url"],
            match_score=scores["overall"],
            confidence="high" if scores["overall"] >= 90 else 
                      "medium" if scores["overall"] >= 80 else "low"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/lyrics/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats(db: Session = Depends(get_db)):
    """Get lyrics cache statistics"""
    try:
        stats = lyrics_cache.get_cache_stats(db)
        return CacheStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

@router.delete("/lyrics/cache/{track_id}")
async def clear_cache_entry(
    track_id: str,
    db: Session = Depends(get_db)
):
    """Clear a specific cache entry"""
    try:
        cached = lyrics_cache.get_cached_lyrics(db, track_id)
        if not cached:
            raise HTTPException(status_code=404, detail="Cache entry not found")
        
        db.delete(cached)
        db.commit()
        
        return {"message": f"Cache entry for {track_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete cache entry: {str(e)}")

@router.get("/lyrics/cache/list")
async def list_cached_entries(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List cached lyrics entries"""
    try:
        from ..models.database import CachedLyrics
        
        entries = db.query(CachedLyrics).offset(offset).limit(limit).all()
        
        return {
            "entries": [
                {
                    "spotify_track_id": entry.spotify_track_id,
                    "artist": entry.artist,
                    "title": entry.title,
                    "has_lyrics": entry.lyrics is not None,
                    "genius_url": entry.genius_url,
                    "cached_at": entry.created_at.isoformat(),
                    "cache_id": entry.id
                }
                for entry in entries
            ],
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list cache entries: {str(e)}")