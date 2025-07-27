# Spotify Mood Blend

A FastAPI application that integrates with Spotify Web API to fetch and analyze your listening history, including top tracks, recently played songs, and audio features.

## Features

- OAuth2 authentication with Spotify
- Fetch user's top tracks (short, medium, long term)
- Get recently played tracks
- Retrieve audio features for tracks (danceability, energy, valence, etc.)
- Batch audio features retrieval

## Setup

### 1. Create Spotify App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Add `http://127.0.0.1:8000/auth/callback` to Redirect URIs
4. Copy your Client ID and Client Secret

### 2. Set Up Virtual Environment

Create and activate a virtual environment:

**macOS/Linux:**
```bash
python3 -m venv spotify-proj
source spotify-proj/bin/activate
```

**Windows:**
```bash
python -m venv spotify-proj
spotify-proj\Scripts\activate
```

### 3. Install Dependencies

With the virtual environment activated:
```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` with your Spotify credentials:
```
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/auth/callback
SECRET_KEY=your_secret_key_here
```

### 5. Run the Application

```bash
python main.py
```

The API will be available at `http://127.0.0.1:8000`

## API Endpoints

### Authentication

**Login with Spotify**
```
GET /auth/login
```
Redirects to Spotify authorization page.

**OAuth Callback**
```
GET /auth/callback?code=xxx&state=xxx
```
Handles the OAuth callback and returns access token.

**Refresh Token**
```
POST /auth/refresh
Body: {"refresh_token": "your_refresh_token"}
```

### Data Endpoints

All data endpoints require Authorization header:
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Get Top Tracks**
```
GET /api/top-tracks?time_range=medium_term&limit=20
```
Parameters:
- `time_range`: short_term, medium_term, long_term
- `limit`: 1-50 (default: 20)

**Get Recently Played**
```
GET /api/recently-played?limit=20
```
Parameters:
- `limit`: 1-50 (default: 20)

**Get Audio Features for a Track**
```
GET /api/audio-features/{track_id}
```

**Get Audio Features for Multiple Tracks**
```
GET /api/audio-features-batch?track_ids=id1,id2,id3
```
Parameters:
- `track_ids`: Comma-separated list of track IDs (max 100)

## Example Usage

1. **Start the authentication flow:**
   ```bash
   curl http://127.0.0.1:8000/auth/login
   ```

2. **After authorization, use the access token:**
   ```bash
   # Get top tracks
   curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        http://127.0.0.1:8000/api/top-tracks
   
   # Get recently played
   curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        http://127.0.0.1:8000/api/recently-played
   
   # Get audio features
   curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        http://127.0.0.1:8000/api/audio-features/TRACK_ID
   ```

## Audio Features Explained

- **danceability**: How suitable a track is for dancing (0.0-1.0)
- **energy**: Perceptual measure of intensity and activity (0.0-1.0)
- **valence**: Musical positiveness/happiness (0.0-1.0)
- **acousticness**: Confidence of track being acoustic (0.0-1.0)
- **instrumentalness**: Predicts if track contains no vocals (0.0-1.0)
- **speechiness**: Presence of spoken words (0.0-1.0)
- **tempo**: Estimated tempo in BPM
- **loudness**: Overall loudness in decibels
- **key**: Pitch class notation (0-11)
- **mode**: Major (1) or minor (0)

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`