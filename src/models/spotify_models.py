from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Track(BaseModel):
    id: str
    name: str
    artists: List[str]
    album: str
    popularity: Optional[int] = None
    preview_url: Optional[str] = None
    external_url: str

class TopTracksResponse(BaseModel):
    tracks: List[Track]
    total: int
    time_range: str

class PlayedTrack(BaseModel):
    played_at: str
    track: Track

class RecentlyPlayedResponse(BaseModel):
    tracks: List[PlayedTrack]
    total: int

class AudioFeaturesResponse(BaseModel):
    track_id: str
    danceability: float
    energy: float
    key: int
    loudness: float
    mode: int
    speechiness: float
    acousticness: float
    instrumentalness: float
    liveness: float
    valence: float
    tempo: float
    duration_ms: int
    time_signature: int