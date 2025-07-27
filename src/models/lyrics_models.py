from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class LyricsRequest(BaseModel):
    spotify_track_id: str
    artist: str
    title: str

class BatchLyricsRequest(BaseModel):
    tracks: List[dict]

class LyricsResponse(BaseModel):
    spotify_track_id: str
    artist: str
    title: str
    lyrics: Optional[str]
    genius_url: Optional[str]
    source: str  # "cache_exact", "cache_fuzzy", "genius_api", "error"
    cached_at: str
    cache_id: int
    error: Optional[str] = None

class CacheStatsResponse(BaseModel):
    total_cached_tracks: int
    tracks_with_lyrics: int
    tracks_without_lyrics: int
    success_rate: float
    recent_additions: int

class GeniusSearchResponse(BaseModel):
    genius_id: Optional[str]
    genius_title: Optional[str]
    genius_artist: Optional[str]
    genius_url: Optional[str]
    match_score: Optional[float]
    confidence: Optional[str]