#!/usr/bin/env python3
"""
Air France Squawk 7700 Monitor

This script monitors live flight data for Air France aircraft
with emergency squawk code 7700 and sends Telegram notifications.
"""

import os
import json
import hashlib
from datetime import datetime
import requests

# Configuration
AIR_FRANCE_ICAO = "AFR"  # Air France ICAO code
SQUAWK_EMERGENCY = "7700"
STATE_FILE = "/tmp/squawk_state.json"


def get_telegram_config():
    """Get Telegram configuration from environment variables."""
    return {
        "bot_token": os.environ.get("TELEGRAM_BOT_TOKEN"),
        "chat_id": os.environ.get("TELEGRAM_CHAT_ID"),
    }


def fetch_squawk_7700_flights():
    """
    Fetch current flights with squawk 7700 from ADS-B Exchange.
    Returns list of Air France flights with emergency squawk.
    """
    url = "https://globe.adsbexchange.com/globecache/squawk/7700/squawk_7700.json"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; SquawkMonitor/1.0)",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        af_flights = []
        aircraft_list = data.get("ac", []) if isinstance(data, dict) else data
        
        for aircraft in aircraft_list:
            flight = aircraft.get("flight", "").strip() if isinstance(aircraft, dict) else ""
            callsign = aircraft.get("call", "").strip() if isinstance(aircraft, dict) else ""
            registration = aircraft.get("r", "").strip() if isinstance(aircraft, dict) else ""
            
            is_air_france = (
                flight.upper().startswith("AF") or
                flight.upper().startswith("AFR") or
                callsign.upper().startswith("AF") or
                callsign.upper().startswith("AFR")
            )
            
            if is_air_france:
                af_flights.append({
                    "flight": flight or callsign,
                    "registration": registration,
                    "altitude": aircraft.get("alt_baro", aircraft.get("altitude", "N/A")),
                    "speed": aircraft.get("gs", aircraft.get("speed", "N/A")),
                    "latitude": aircraft.get("lat", "N/A"),
                    "longitude": aircraft.get("lon", "N/A"),
                    "squawk": aircraft.get("squawk", "7700"),
                    "hex": aircraft.get("hex", "unknown"),
                    "type": aircraft.get("t", aircraft.get("type", "N/A")),
                    "origin": aircraft.get("from", "N/A"),
                    "destination": aircraft.get("to", "N/A"),
                })
        
        return af_flights
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching flight data: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        return []


def get_flight_hash(flight):
    """Generate a unique hash for a flight to track alerts."""
    unique_str = f"{flight['hex']}_{flight['flight']}"
    return hashlib.md5(unique_str.encode()).hexdigest()


def load_previous_state():
    """Load previously alerted flights."""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {"alerted_flights": []}


def save_state(state):
    """Save current state to file."""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f)
    except Exception as e:
        print(f"Warning: Could not save state: {e}")


def send_telegram_notification(flight, config):
    """Send Telegram notification about the emergency."""
    if not config["bot_token"] or not config["chat_id"]:
        print("Telegram configuration missing. Skipping notification.")
        print(f"ALERT: Air France flight {flight['flight']} squawking 7700!")
        return False
    
    message = f"""\U0001F6A8 <b>AIR FRANCE EMERGENCY ALERT</b> \U0001F6A8

<b>Flight {flight['flight']}</b> is squawking 7700!

\U00002708 <b>Flight Details:</b>
Flight: <code>{flight['flight']}</code>
Registration: <code>{flight['registration']}</code>
Aircraft: <code>{flight['type']}</code>
Squawk: <code>{flight['squawk']}</code>

\U0001F4CD <b>Position:</b>
Altitude: {flight['altitude']} ft
Speed: {flight['speed']} kts
Lat: {flight['latitude']}
Lon: {flight['longitude']}

\U0001F6EB Route: {flight['origin']} -> {flight['destination']}

\U0001F517 <a href="https://globe.adsbexchange.com/?icao={flight['hex']}">Track Live</a>

\U0001F551 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"""
    
    try:
        url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
        payload = {
            "chat_id": config["chat_id"],
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        print(f"Telegram notification sent for flight {flight['flight']}")
        return True
        
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False


def main():
    print(f"Checking for Air France squawk 7700 at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    config = get_telegram_config()
    state = load_previous_state()
    af_flights = fetch_squawk_7700_flights()
    
    if not af_flights:
        print("No Air France flights currently squawking 7700.")
        state["alerted_flights"] = []
        save_state(state)
        return
    
    print(f"Found {len(af_flights)} Air France flight(s) with squawk 7700!")
    
    new_alerts = []
    for flight in af_flights:
        flight_hash = get_flight_hash(flight)
        
        if flight_hash not in state["alerted_flights"]:
            print(f"New emergency: {flight['flight']}")
            send_telegram_notification(flight, config)
            new_alerts.append(flight_hash)
        else:
            print(f"Already alerted for flight {flight['flight']}")
    
    state["alerted_flights"].extend(new_alerts)
    save_state(state)
    
    print("Check complete.")


if __name__ == "__main__":
    main()
