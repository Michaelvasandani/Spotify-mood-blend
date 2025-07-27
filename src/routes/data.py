from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional, List
import spotipy

from ..utils.spotify_client import SpotifyClient
from ..models.spotify_models import TopTracksResponse, RecentlyPlayedResponse, AudioFeaturesResponse

router = APIRouter()

def get_spotify_client_from_token(token: str) -> spotipy.Spotify:
    spotify_client = SpotifyClient()
    return spotify_client.get_spotify_client(token)

@router.get("/top-tracks", response_model=TopTracksResponse)
async def get_top_tracks(
    authorization: str = Header(...),
    time_range: str = Query("medium_term", description="Time range: short_term, medium_term, long_term"),
    limit: int = Query(20, ge=1, le=50)
):
    try:
        token = authorization.replace("Bearer ", "")
        sp = get_spotify_client_from_token(token)
        
        results = sp.current_user_top_tracks(time_range=time_range, limit=limit)
        
        tracks = []
        for item in results['items']:
            track = {
                "id": item['id'],
                "name": item['name'],
                "artists": [artist['name'] for artist in item['artists']],
                "album": item['album']['name'],
                "popularity": item['popularity'],
                "preview_url": item['preview_url'],
                "external_url": item['external_urls']['spotify']
            }
            tracks.append(track)
        
        return TopTracksResponse(
            tracks=tracks,
            total=len(tracks),
            time_range=time_range
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch top tracks: {str(e)}")

@router.get("/recently-played", response_model=RecentlyPlayedResponse)
async def get_recently_played(
    authorization: str = Header(...),
    limit: int = Query(20, ge=1, le=50)
):
    try:
        token = authorization.replace("Bearer ", "")
        sp = get_spotify_client_from_token(token)
        
        results = sp.current_user_recently_played(limit=limit)
        
        tracks = []
        for item in results['items']:
            track = item['track']
            played_item = {
                "played_at": item['played_at'],
                "track": {
                    "id": track['id'],
                    "name": track['name'],
                    "artists": [artist['name'] for artist in track['artists']],
                    "album": track['album']['name'],
                    "preview_url": track['preview_url'],
                    "external_url": track['external_urls']['spotify']
                }
            }
            tracks.append(played_item)
        
        return RecentlyPlayedResponse(
            tracks=tracks,
            total=len(tracks)
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch recently played: {str(e)}")

@router.get("/audio-features/{track_id}", response_model=AudioFeaturesResponse)
async def get_audio_features(
    track_id: str,
    authorization: str = Header(...)
):
    try:
        token = authorization.replace("Bearer ", "")
        sp = get_spotify_client_from_token(token)
        
        features = sp.audio_features(track_id)[0]
        
        if not features:
            raise HTTPException(status_code=404, detail="Audio features not found for this track")
        
        return AudioFeaturesResponse(
            track_id=features['id'],
            danceability=features['danceability'],
            energy=features['energy'],
            key=features['key'],
            loudness=features['loudness'],
            mode=features['mode'],
            speechiness=features['speechiness'],
            acousticness=features['acousticness'],
            instrumentalness=features['instrumentalness'],
            liveness=features['liveness'],
            valence=features['valence'],
            tempo=features['tempo'],
            duration_ms=features['duration_ms'],
            time_signature=features['time_signature']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch audio features: {str(e)}")

@router.get("/audio-features-batch")
async def get_audio_features_batch(
    track_ids: str = Query(..., description="Comma-separated list of track IDs"),
    authorization: str = Header(...)
):
    try:
        token = authorization.replace("Bearer ", "")
        sp = get_spotify_client_from_token(token)
        
        ids_list = track_ids.split(',')
        if len(ids_list) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 tracks allowed per request")
        
        features_list = sp.audio_features(ids_list)
        
        result = []
        for features in features_list:
            if features:
                result.append({
                    "track_id": features['id'],
                    "danceability": features['danceability'],
                    "energy": features['energy'],
                    "key": features['key'],
                    "loudness": features['loudness'],
                    "mode": features['mode'],
                    "speechiness": features['speechiness'],
                    "acousticness": features['acousticness'],
                    "instrumentalness": features['instrumentalness'],
                    "liveness": features['liveness'],
                    "valence": features['valence'],
                    "tempo": features['tempo'],
                    "duration_ms": features['duration_ms'],
                    "time_signature": features['time_signature']
                })
        
        return {"audio_features": result, "total": len(result)}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch audio features: {str(e)}")