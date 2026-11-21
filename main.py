import os
import requests
import json
from apify_client import ApifyClient

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
APIFY_TOKEN = os.environ["APIFY_TOKEN"]
DATASET_ID = "YOUR_DATASET_ID_HERE" # Paste your Dataset ID here

CONFIG_FILE = "target_config.json"

def get_telegram_updates(last_update_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"offset": last_update_id + 1, "timeout": 10}
    r = requests.get(url, params=params)
    return r.json()

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": message})

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    # Default fallback if no config exists yet
    return {"city": "mumbai", "movie": "avengers", "theatre": "pvr", "last_update_id": 0}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def process_telegram_commands(config):
    print("Checking Telegram for new commands...")
    updates = get_telegram_updates(config.get("last_update_id", 0))
    
    if not updates.get("ok"):
        print("Error getting updates:", updates)
        return config

    for update in updates.get("result", []):
        # Mark this message as read so we don't process it again
        config["last_update_id"] = update["update_id"]
        
        # Ensure it's a text message
        if "message" not in update or "text" not in update["message"]:
            continue
            
        text = update["message"]["text"].strip()
        
        # Command format: /set mumbai avengers pvr
        if text.startswith("/set"):
            parts = text.split()
            if len(parts) >= 4:
                config["city"] = parts[1].lower()
                config["movie"] = parts[2].lower()
                # Join the rest in case the theatre name has spaces
                config["theatre"] = " ".join(parts[3:]).lower() 
                
                save_config(config)
                send_telegram_message(f"✅ Targets updated!\nCity: {config['city']}\nMovie: {config['movie']}\nTheatre: {config['theatre']}")
                print("Targets updated via Telegram.")
            else:
                send_telegram_message("❌ Format error. Use:\n/set <city> <movie> <theatre>\nExample: /set mumbai deadpool pvr")
                
    save_config(config)
    return config

def check_bookmyshow(config):
    client = ApifyClient(APIFY_TOKEN)
    print(f"Fetching Dataset: {DATASET_ID}...")
    
    dataset_items = client.dataset(DATASET_ID).list_items(limit=100).items
    
    if not dataset_items:
        print("Dataset is empty.")
        return

    found = False
    for item in dataset_items:
        item_string = str(item).lower()
        
        # Check if the scraped data contains the city, movie, and theatre you set
        if (config["movie"] in item_string and 
            config["theatre"] in item_string):
            
            # Simple check to see if it actually has showtimes
            if "time" in item_string or "date" in item_string:
                print(f"Match found! Data: {item}")
                msg = f"🚨 Match Found!\nTarget: {config['movie']} at {config['theatre']}\nCheck BookMyShow!"
                send_telegram_message(msg)
                found = True
                break
                
    if not found:
        print(f"No matches for {config['movie']} at {config['theatre']} yet.")

if __name__ == "__main__":
    # 1. Load current settings
    current_config = load_config()
    
    # 2. Check if you sent a new /set command
    current_config = process_telegram_commands(current_config)
    
    # 3. Check the Apify data against your settings
    check_bookmyshow(current_config)
