import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import Counter
from datetime import datetime

# USER CLIENT: to get songs they are listening to and stuff
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="b03e39464f6549d0a8b182994115dc73",
    client_secret="bb2e540b1e1d418d8a0007ac92685422",
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

        if played_at != date:
            continue

        artist_id = item['track']['artists'][0]['id']
        try:
            artist = sp.artist(artist_id)
            genres = artist.get('genres', [])
            
            genre_counter.update(genres)
        except:
            pass
    return dict(genre_counter)


