import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import Optional

class SpotifyClient:
    def __init__(self):
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")
        
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError("Missing Spotify API credentials in environment variables")
        
        self.scope = " ".join([
            "user-read-recently-played",
            "user-top-read",
            "user-read-currently-playing",
            "user-read-playback-state",
            "user-library-read"
        ])
    
    def get_auth_url(self, state: Optional[str] = None) -> str:
        sp_oauth = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
            state=state
        )
        return sp_oauth.get_authorize_url()
    
    def get_access_token(self, code: str) -> dict:
        sp_oauth = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope
        )
        token_info = sp_oauth.get_access_token(code, as_dict=True)
        return token_info
    
    def refresh_access_token(self, refresh_token: str) -> dict:
        sp_oauth = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri
        )
        token_info = sp_oauth.refresh_access_token(refresh_token)
        return token_info
    
    def get_spotify_client(self, token: str) -> spotipy.Spotify:
        return spotipy.Spotify(auth=token)