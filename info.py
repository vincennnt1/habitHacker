import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import Counter
from datetime import datetime, timedelta
# import os

# from dotenv import load_dotenv
# load_dotenv()

# USER CLIENT: to get songs they are listening to and stuff
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="b03e39464f6549d0a8b182994115dc73",
    client_secret="bb2e540b1e1d418d8a0007ac92685422",
    redirect_uri="http://127.0.0.1:8888/callback",
    scope="user-read-recently-played"
))

# Get recent tracks, we'll use 50
def getGenres(date):    
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
    return genre_counter.most_common(1)[0][0]


# print(getGenres(sp, datetime.now().date()))

# LOCATION GATHERING
import requests

def get_location():
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        location = data.get("loc", "0,0").split(",")
        city = data.get("city", "")
        region = data.get("region", "")
        country = data.get("country", "")
        return {
            "latitude": location[0],
            "longitude": location[1],
            "city": city,
            "region": region,
            "country": country
        }
    except Exception as e:
        print("Error getting location:", e)
        return None
    

# Weather condition mapping
weather_map = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Rain showers",
    81: "Heavy rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail"
}


def get_weather(loc):
    url = f"https://api.open-meteo.com/v1/forecast"
    params = {
    "latitude": loc['latitude'],
    "longitude": loc['longitude'],
    "start_date": datetime.now().strftime('%Y-%m-%d'),
    "end_date": datetime.now().strftime('%Y-%m-%d'),
    "daily": "weathercode",
    "timezone": "America/Toronto"
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data