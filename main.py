import requests
import os
import json
from info import get_location, get_weather, getGenres, weather_map
import csv
from datetime import datetime
import joblib
import re
import numpy as np

# used for sentiment analysis entry preprocessing
def clean(text):
    text = text.lower()
    text = re.sub(r"http\S+|www\S+|https\S+", '', text)
    text = re.sub(r"@\w+", '', text)
    text = re.sub(r"#", '', text)
    text = re.sub(r"\s+", ' ', text).strip()
    return text

# loading model & Encoder (MUST DO ON STARTUP)
mod = joblib.load("model.job")
le = joblib.load("label_encoder.job")

# checks if location has changed, or if there is no location currently set
location_data = get_location()
if not os.path.exists("location.json") or os.path.getsize("location.json") == 0:
    if location_data:
        with open("location.json", "w") as f:
            json.dump(location_data, f, indent=4)
else:
    location_data = get_location()
    if location_data:
        with open("location.json", "r") as f:
            old_location = json.load(f)
            city = location_data.get("city", "Unknown")
            if location_data['city'] != city:
                json.dump(location_data, f, indent=4)

# submit's an entry to user_info.csv
def submit(entry):
    with open("location.json", "r") as f:
        loc = json.load(f)
        weather_data = get_weather(loc)

        clean_entry = [clean(entry)]
        # predicts probabilities
        pred_proba = mod.predict_proba(clean_entry)
        # gets top probaility
        pred_index = np.argmax(pred_proba, axis=1)
    
    code = weather_data['daily']['weathercode'][0]
    if (code == 0 or code == 1):
        weather = "Sunny"
    elif (code == 2 or code == 3):
        weather = "Cloudy"
    elif (code == 45 or code == 48):
        weather = "Foggy"
    elif (code >= 71 and code <= 75):
        weather = "Snowy"
    elif (code >= 51 and code <= 80):
        weather = "Rainy"
    else:
        weather = "Stormy"

    row = [datetime.now().strftime('%Y-%m-%d'), 
           weather_map.get(code),
           weather,
            getGenres(datetime.now()),
            entry,
            le.inverse_transform(pred_index)[0]]
    
    with open("user_info.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(row)
        
# test
submit("I am feeling quite horrible today.")