import os
import requests
from apify_client import ApifyClient

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
APIFY_TOKEN = os.environ["APIFY_TOKEN"]

# --- EDIT THESE ---
TARGET_CITY = "mumbai"
TARGET_MOVIE_KEYWORD = "Avengers"
TARGET_THEATRE_KEYWORD = "PVR"
# ------------------

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": CHAT_ID, "text": message})
    print("Telegram response:", r.status_code, r.text)

def check_bookmyshow():
    client = ApifyClient(APIFY_TOKEN)
    run_input = {
        "mode": "search",
        "city": TARGET_CITY,
        "category": "movies",
        "maxItems": 50,
        "fetchDetails": True,
    }
    print("Starting Apify run...")
    run = client.actor("abotapi/bookmyshow-scraper").call(run_input=run_input)
    print("Apify run finished:", run.status)

    found = False
    count = 0
    for item in client.dataset(run.default_dataset_id).iterate_items():
        count += 1
        movie_name = item.get("movie", "") or item.get("title", "")
        venue = item.get("venueName", "") or item.get("venue", "")
        print(f"[{count}] movie='{movie_name}' venue='{venue}'")

        if TARGET_MOVIE_KEYWORD.lower() in movie_name.lower() \
           and TARGET_THEATRE_KEYWORD.lower() in venue.lower():
            if item.get("showDateTimeUtc") or item.get("timeText"):
                msg = f"🚨 Bookings OPEN!\nMovie: {movie_name}\nTheatre: {venue}\nBook now!"
                print(msg)
                send_telegram_alert(msg)
                found = True
                break

    if not found:
        print("No matching showtimes yet.")

if __name__ == "__main__":
    check_bookmyshow()
