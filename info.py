import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import Counter
from datetime import datetime, timedelta
import os

from dotenv import load_dotenv
load_dotenv()

# USER CLIENT: to get songs they are listening to and stuff
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="user-read-recently-played"
))

# Get recent tracks, we'll use 50
def getGenres(sp, date):    
    results = sp.current_user_recently_played(limit=50)
    genre_counter = Counter()

    for item in results['items']:
        played_at = item['played_at']
        played_at = played_at[:10]

        if played_at != date.strftime("%Y-%m-%d"):
            continue

        artist_id = item['track']['artists'][0]['id']
        try:
            artist = sp.artist(artist_id)
            genres = artist.get('genres', [])
            
            genre_counter.update(genres)
        except:
            pass
    return dict(genre_counter)


print(getGenres(sp, datetime.now().date()))