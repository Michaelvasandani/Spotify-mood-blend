from rapidfuzz import fuzz, process
from typing import List, Dict, Tuple, Optional
import re

class FuzzyMatcher:
    def __init__(self, threshold: int = 80):
        self.threshold = threshold
    
    def clean_string(self, text: str) -> str:
        """Clean string for better matching"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove common variations
        text = re.sub(r'\s*\(feat\.?\s+[^)]+\)', '', text)  # Remove (feat. artist)
        text = re.sub(r'\s*\[feat\.?\s+[^]]+\]', '', text)  # Remove [feat. artist]
        text = re.sub(r'\s*\(ft\.?\s+[^)]+\)', '', text)    # Remove (ft. artist)
        text = re.sub(r'\s*\[ft\.?\s+[^]]+\]', '', text)    # Remove [ft. artist]
        text = re.sub(r'\s*\(with\s+[^)]+\)', '', text)     # Remove (with artist)
        
        # Remove remix/version indicators
        text = re.sub(r'\s*\(.*remix.*\)', '', text)
        text = re.sub(r'\s*\(.*version.*\)', '', text)
        text = re.sub(r'\s*\(.*edit.*\)', '', text)
        text = re.sub(r'\s*\(live.*\)', '', text)
        text = re.sub(r'\s*\(acoustic.*\)', '', text)
        text = re.sub(r'\s*\(radio.*\)', '', text)
        
        # Remove brackets and parentheses content
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\(.*?\)', '', text)
        
        # Remove extra whitespace and punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def clean_artist_name(self, artist: str) -> str:
        """Clean artist name for matching"""
        if not artist:
            return ""
        
        # Handle multiple artists
        artist = artist.lower()
        
        # Remove featuring artists from main artist field
        artist = re.sub(r'\s*feat\.?\s+.*', '', artist)
        artist = re.sub(r'\s*ft\.?\s+.*', '', artist)
        artist = re.sub(r'\s*featuring\s+.*', '', artist)
        artist = re.sub(r'\s*with\s+.*', '', artist)
        artist = re.sub(r'\s*&\s+.*', '', artist)  # Take first artist if multiple
        artist = re.sub(r'\s*,\s+.*', '', artist)  # Take first artist if comma-separated
        
        # Clean punctuation
        artist = re.sub(r'[^\w\s]', ' ', artist)
        artist = re.sub(r'\s+', ' ', artist)
        
        return artist.strip()
    
    def create_search_variants(self, artist: str, title: str) -> List[str]:
        """Create different search query variants for better matching"""
        clean_artist = self.clean_artist_name(artist)
        clean_title = self.clean_string(title)
        
        variants = [
            f"{clean_artist} {clean_title}",
            f"{artist} {title}",  # Original
            f"{clean_title} {clean_artist}",  # Reversed order
            clean_title,  # Title only
        ]
        
        # Remove duplicates and empty strings
        return list(filter(None, list(dict.fromkeys(variants))))
    
    def match_song(self, spotify_artist: str, spotify_title: str, genius_results: List[Dict]) -> Optional[Dict]:
        """Match Spotify track with Genius search results"""
        if not genius_results:
            return None
        
        # Create search variants for the Spotify track
        spotify_variants = self.create_search_variants(spotify_artist, spotify_title)
        
        best_match = None
        best_score = 0
        
        for result in genius_results:
            genius_artist = result.get("primary_artist", {}).get("name", "")
            genius_title = result.get("title", "")
            
            # Create variants for this Genius result
            genius_variants = self.create_search_variants(genius_artist, genius_title)
            
            # Test all combinations
            for spotify_variant in spotify_variants:
                for genius_variant in genius_variants:
                    # Use different scoring methods
                    scores = [
                        fuzz.ratio(spotify_variant, genius_variant),
                        fuzz.partial_ratio(spotify_variant, genius_variant),
                        fuzz.token_sort_ratio(spotify_variant, genius_variant),
                        fuzz.token_set_ratio(spotify_variant, genius_variant)
                    ]
                    
                    # Take the best score from all methods
                    max_score = max(scores)
                    
                    if max_score > best_score:
                        best_score = max_score
                        best_match = result
        
        # Return match only if it meets threshold
        if best_score >= self.threshold:
            return {
                "match": best_match,
                "score": best_score,
                "confidence": "high" if best_score >= 90 else "medium" if best_score >= 80 else "low"
            }
        
        return None
    
    def match_artist_title(self, spotify_artist: str, spotify_title: str, 
                          genius_artist: str, genius_title: str) -> Dict[str, float]:
        """Get detailed matching scores between two tracks"""
        
        # Clean both versions
        clean_spotify = f"{self.clean_artist_name(spotify_artist)} {self.clean_string(spotify_title)}"
        clean_genius = f"{self.clean_artist_name(genius_artist)} {self.clean_string(genius_title)}"
        
        # Original versions
        original_spotify = f"{spotify_artist} {spotify_title}"
        original_genius = f"{genius_artist} {genius_title}"
        
        # Calculate various scores
        scores = {
            "ratio": fuzz.ratio(clean_spotify, clean_genius),
            "partial_ratio": fuzz.partial_ratio(clean_spotify, clean_genius),
            "token_sort_ratio": fuzz.token_sort_ratio(clean_spotify, clean_genius),
            "token_set_ratio": fuzz.token_set_ratio(clean_spotify, clean_genius),
            "original_ratio": fuzz.ratio(original_spotify, original_genius),
        }
        
        # Overall confidence score
        scores["overall"] = max(scores["ratio"], scores["token_sort_ratio"], scores["token_set_ratio"])
        
        return scores