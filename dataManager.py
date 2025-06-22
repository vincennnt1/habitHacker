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

# update, called whenever a new submission is made to look for patterns
def update(row):
    with open("user.json", "r", encoding="utf-8") as f:
        patterns = json.load(f)

    # Normalize inputs
    sentiment = row[7].lower()
    weather = row[4].title()
    genre = row[5].lower()

    patterns[sentiment]["weather"][weather] += 1

    if genre in patterns[sentiment]["genres"]:
        patterns[sentiment]["genres"][genre] += 1
    else:
        patterns[sentiment]["genres"][genre] = 1

    with open("user.json", "w", encoding="utf-8") as f:
        json.dump(patterns, f, indent=4)


# submit's an entry to user_info.csv
def submit(entry, title):
    with open("location.json", "r") as f:
        loc = json.load(f)
        weather_data = get_weather(loc)

        clean_entry = [clean(entry)]
        # predicts probabilities
        pred_proba = mod.predict_proba(clean_entry)
        # gets top probaility
        pred_index = np.argmax(pred_proba, axis=1)
    
    with open("user.json", "r") as f:
        user = json.load(f)
        entries = user["ENTRIES_NUM"]
    
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

    row = [ entries,
            title,
            datetime.now().strftime('%Y-%m-%d'), 
            weather_map.get(code),
            weather,
            getGenres(datetime.now()),
            entry.replace('\n', ' ').strip(),
            le.inverse_transform(pred_index)[0]]
    
    with open("user_info.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(row)
    
    with open("user.json", "r", encoding="utf-8") as f:
        user = json.load(f)
        user["ENTRIES_NUM"] += 1
    with open("user.json", "w", encoding="utf-8") as f:
        json.dump(user, f, indent=4)
    update(row)
        
# test
# submit("I am feeling quite horrible today.")

# remove an entry based of the id NUM
def remove(num):
    with open("user_info.csv", "r", newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))

    for row in rows[1:]:
        if row[0] == str(num):
            sentiment = row[7].lower()
            weather = row[4].title()
            genre = row[5].lower()
            with open("user.json", "r", encoding="utf-8") as f:
                patterns = json.load(f)
                
            patterns[sentiment]["weather"][weather] -= 1
            patterns[sentiment]["genres"][genre] -= 1
            
            with open("user.json", "w", encoding="utf-8") as f:
                json.dump(patterns, f, indent=4)
            break

    header = rows[0]
    new_rows = [row for row in rows[1:] if row[0] != str(num)]

    with open("user_info.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(header)
        writer.writerows(new_rows)

# test for remove
#remove(4)

def get_recent_entries(n=10):
    try:
        with open("user_info.csv", "r", encoding="utf-8") as f:
            reader = list(csv.reader(f))
            headers = reader[0]
            rows = reader[1:]
            last_n = rows[-n:] if len(rows) >= n else rows
            return [headers] + last_n  # Add headers to top
    except Exception as e:
        return [["Error", str(e)]]