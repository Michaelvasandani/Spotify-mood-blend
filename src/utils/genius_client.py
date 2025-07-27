import os
import requests
import lyricsgenius
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
import time

class GeniusClient:
    def __init__(self):
        self.access_token = os.getenv("GENIUS_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("GENIUS_ACCESS_TOKEN environment variable is required")
        
        self.genius = lyricsgenius.Genius(self.access_token)
        self.genius.verbose = False
        self.genius.remove_section_headers = True
        self.genius.skip_non_songs = True
        self.genius.excluded_terms = ["(Remix)", "(Live)", "(Acoustic)", "(Demo)"]
        
        self.base_url = "https://api.genius.com"
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.6  # 100 requests per minute max
    
    def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def search_song(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """Search for a song on Genius"""
        try:
            self._rate_limit()
            
            # Clean up search terms
            search_query = f"{artist} {title}".strip()
            
            # Use direct API search for better control
            search_url = f"{self.base_url}/search"
            params = {"q": search_query}
            
            response = requests.get(search_url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data["response"]["hits"]:
                # Return the first hit
                hit = data["response"]["hits"][0]
                return {
                    "id": hit["result"]["id"],
                    "title": hit["result"]["title"],
                    "artist": hit["result"]["primary_artist"]["name"],
                    "url": hit["result"]["url"],
                    "lyrics_state": hit["result"]["lyrics_state"]
                }
            
            return None
            
        except Exception as e:
            print(f"Error searching for song {artist} - {title}: {str(e)}")
            return None
    
    def get_song_lyrics(self, song_url: str) -> Optional[str]:
        """Scrape lyrics from Genius song page"""
        try:
            self._rate_limit()
            
            response = requests.get(song_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for lyrics containers (Genius uses different classes)
            lyrics_containers = [
                soup.find('div', class_='lyrics'),
                soup.find('div', {'data-lyrics-container': 'true'}),
                soup.find('div', class_='Lyrics__Container-sc-1ynbvzw-6')
            ]
            
            # Try different selectors
            if not any(lyrics_containers):
                lyrics_divs = soup.find_all('div', class_=lambda x: x and 'lyrics' in x.lower())
                if lyrics_divs:
                    lyrics_containers = [lyrics_divs[0]]
            
            for container in lyrics_containers:
                if container:
                    # Extract text and clean it up
                    lyrics_text = container.get_text(separator='\n', strip=True)
                    if lyrics_text and len(lyrics_text) > 50:  # Basic validation
                        return lyrics_text
            
            # If no lyrics found, try alternative method with lyricsgenius
            try:
                song = self.genius.search_song(title="", artist="", song_url=song_url)
                if song and song.lyrics:
                    return song.lyrics
            except:
                pass
            
            return None
            
        except Exception as e:
            print(f"Error getting lyrics from {song_url}: {str(e)}")
            return None
    
    def search_and_get_lyrics(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """Search for a song and get its lyrics"""
        try:
            # First search for the song
            song_info = self.search_song(artist, title)
            if not song_info:
                return None
            
            # Check if lyrics are available
            if song_info.get("lyrics_state") != "complete":
                return {
                    "song_info": song_info,
                    "lyrics": None,
                    "error": "Lyrics not available"
                }
            
            # Get the lyrics
            lyrics = self.get_song_lyrics(song_info["url"])
            
            return {
                "song_info": song_info,
                "lyrics": lyrics,
                "error": None if lyrics else "Could not extract lyrics"
            }
            
        except Exception as e:
            return {
                "song_info": None,
                "lyrics": None,
                "error": str(e)
            }