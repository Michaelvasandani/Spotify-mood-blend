from sqlalchemy.orm import Session
from typing import Optional, List
from ..models.database import CachedLyrics, get_db
from ..utils.genius_client import GeniusClient
from ..utils.fuzzy_matcher import FuzzyMatcher
from datetime import datetime, timedelta

class LyricsCache:
    def __init__(self):
        self.genius_client = GeniusClient()
        self.fuzzy_matcher = FuzzyMatcher(threshold=80)
    
    def get_cached_lyrics(self, db: Session, spotify_track_id: str) -> Optional[CachedLyrics]:
        """Get lyrics from cache by Spotify track ID"""
        return db.query(CachedLyrics).filter(
            CachedLyrics.spotify_track_id == spotify_track_id
        ).first()
    
    def search_cached_lyrics(self, db: Session, artist: str, title: str, 
                           threshold: int = 85) -> Optional[CachedLyrics]:
        """Search cache using fuzzy matching on artist and title"""
        # Get all cached entries
        cached_entries = db.query(CachedLyrics).all()
        
        best_match = None
        best_score = 0
        
        for entry in cached_entries:
            # Calculate similarity score
            scores = self.fuzzy_matcher.match_artist_title(
                artist, title, entry.artist, entry.title
            )
            
            if scores["overall"] > best_score and scores["overall"] >= threshold:
                best_score = scores["overall"]
                best_match = entry
        
        return best_match
    
    def cache_lyrics(self, db: Session, spotify_track_id: str, artist: str, 
                    title: str, genius_id: Optional[str] = None, 
                    genius_url: Optional[str] = None, 
                    lyrics: Optional[str] = None) -> CachedLyrics:
        """Cache lyrics in database"""
        
        # Check if already exists
        existing = self.get_cached_lyrics(db, spotify_track_id)
        if existing:
            # Update existing entry
            existing.artist = artist
            existing.title = title
            existing.genius_id = genius_id
            existing.genius_url = genius_url
            existing.lyrics = lyrics
            existing.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            return existing
        
        # Create new entry
        cached_entry = CachedLyrics(
            spotify_track_id=spotify_track_id,
            artist=artist,
            title=title,
            genius_id=genius_id,
            genius_url=genius_url,
            lyrics=lyrics
        )
        
        db.add(cached_entry)
        db.commit()
        db.refresh(cached_entry)
        return cached_entry
    
    def fetch_and_cache_lyrics(self, db: Session, spotify_track_id: str, 
                              artist: str, title: str) -> dict:
        """Fetch lyrics from Genius and cache them"""
        
        try:
            # First check exact cache match
            cached = self.get_cached_lyrics(db, spotify_track_id)
            if cached:
                return {
                    "source": "cache_exact",
                    "lyrics": cached.lyrics,
                    "genius_url": cached.genius_url,
                    "cached_at": cached.created_at.isoformat(),
                    "cache_id": cached.id
                }
            
            # Then check fuzzy cache match
            fuzzy_cached = self.search_cached_lyrics(db, artist, title)
            if fuzzy_cached:
                # Update the spotify_track_id for this cached entry
                self.cache_lyrics(
                    db, spotify_track_id, artist, title,
                    fuzzy_cached.genius_id, fuzzy_cached.genius_url,
                    fuzzy_cached.lyrics
                )
                return {
                    "source": "cache_fuzzy",
                    "lyrics": fuzzy_cached.lyrics,
                    "genius_url": fuzzy_cached.genius_url,
                    "cached_at": fuzzy_cached.created_at.isoformat(),
                    "cache_id": fuzzy_cached.id
                }
            
            # Not in cache, fetch from Genius
            result = self.genius_client.search_and_get_lyrics(artist, title)
            
            genius_id = None
            genius_url = None
            lyrics = None
            
            if result and result.get("song_info"):
                genius_id = str(result["song_info"]["id"])
                genius_url = result["song_info"]["url"]
                lyrics = result.get("lyrics")
            
            # Cache the result (even if no lyrics found)
            cached_entry = self.cache_lyrics(
                db, spotify_track_id, artist, title,
                genius_id, genius_url, lyrics
            )
            
            return {
                "source": "genius_api",
                "lyrics": lyrics,
                "genius_url": genius_url,
                "error": result.get("error") if result else "No results found",
                "cached_at": cached_entry.created_at.isoformat(),
                "cache_id": cached_entry.id
            }
            
        except Exception as e:
            # Cache the failed attempt
            cached_entry = self.cache_lyrics(
                db, spotify_track_id, artist, title,
                None, None, None
            )
            
            return {
                "source": "error",
                "lyrics": None,
                "error": str(e),
                "cached_at": cached_entry.created_at.isoformat(),
                "cache_id": cached_entry.id
            }
    
    def batch_fetch_lyrics(self, db: Session, tracks: List[dict]) -> List[dict]:
        """Batch fetch lyrics for multiple tracks"""
        results = []
        
        for track in tracks:
            spotify_id = track.get("id")
            artist = track.get("artists", [])
            title = track.get("name")
            
            # Handle artist list
            if isinstance(artist, list):
                artist = artist[0] if artist else "Unknown Artist"
            
            if not all([spotify_id, artist, title]):
                results.append({
                    "spotify_track_id": spotify_id,
                    "artist": artist,
                    "title": title,
                    "error": "Missing required track information"
                })
                continue
            
            # Fetch lyrics
            result = self.fetch_and_cache_lyrics(db, spotify_id, artist, title)
            result.update({
                "spotify_track_id": spotify_id,
                "artist": artist,
                "title": title
            })
            
            results.append(result)
        
        return results
    
    def get_cache_stats(self, db: Session) -> dict:
        """Get cache statistics"""
        total_entries = db.query(CachedLyrics).count()
        entries_with_lyrics = db.query(CachedLyrics).filter(
            CachedLyrics.lyrics.isnot(None)
        ).count()
        
        recent_entries = db.query(CachedLyrics).filter(
            CachedLyrics.created_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        return {
            "total_cached_tracks": total_entries,
            "tracks_with_lyrics": entries_with_lyrics,
            "tracks_without_lyrics": total_entries - entries_with_lyrics,
            "success_rate": (entries_with_lyrics / total_entries * 100) if total_entries > 0 else 0,
            "recent_additions": recent_entries
        }