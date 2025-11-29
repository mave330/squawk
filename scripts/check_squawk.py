#!/usr/bin/env python3
"""
Air France Squawk 7700 Monitor

This script monitors live flight data for Air France aircraft
with emergency squawk code 7700 and sends email notifications.
"""

import os
import json
import smtplib
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import requests

# Configuration
AIR_FRANCE_ICAO = "AFR"  # Air France ICAO code
SQUAWK_EMERGENCY = "7700"
STATE_FILE = "/tmp/squawk_state.json"


def get_email_config():
    """Get email configuration from environment variables."""
    return {
        "address": os.environ.get("EMAIL_ADDRESS"),
        "password": os.environ.get("EMAIL_PASSWORD"),
        "smtp_server": os.environ.get("SMTP_SERVER", "smtp.gmail.com"),
        "smtp_port": int(os.environ.get("SMTP_PORT", "587")),
    }


def fetch_squawk_7700_flights():
    """
    Fetch current flights with squawk 7700 from ADS-B Exchange.
    Returns list of Air France flights with emergency squawk.
    """
    # Using ADS-B Exchange public API for squawk 7700
    url = "https://globe.adsbexchange.com/globecache/squawk/7700/squawk_7700.json"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; SquawkMonitor/1.0)",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Filter for Air France flights
        af_flights = []
        aircraft_list = data.get("ac", []) if isinstance(data, dict) else data
        
        for aircraft in aircraft_list:
            # Check if it's an Air France flight
            flight = aircraft.get("flight", "").strip() if isinstance(aircraft, dict) else ""
            callsign = aircraft.get("call", "").strip() if isinstance(aircraft, dict) else ""
            registration = aircraft.get("r", "").strip() if isinstance(aircraft, dict) else ""
            
            # Air France flights start with AF or AFR
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


def send_email_notification(flight, config):
    """Send email notification about the emergency."""
    if not config["address"] or not config["password"]:
        print("Email configuration missing. Skipping notification.")
        print(f"ALERT: Air France flight {flight['flight']} squawking 7700!")
        return False
    
    subject = f"ALERT: Air France {flight['flight']} - SQUAWK 7700 EMERGENCY"
    
    body = f"""
AIR FRANCE EMERGENCY ALERT
==========================

An Air France flight is currently squawking 7700 (General Emergency).

Flight Details:
---------------
Flight Number: {flight['flight']}
Registration: {flight['registration']}
Aircraft Type: {flight['type']}
Squawk Code: {flight['squawk']}

Position Information:
--------------------
Altitude: {flight['altitude']} ft
Ground Speed: {flight['speed']} kts
Latitude: {flight['latitude']}
Longitude: {flight['longitude']}

Route Information:
-----------------
Origin: {flight['origin']}
Destination: {flight['destination']}

Tracking:
---------
Hex Code: {flight['hex']}
Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Track live at:
https://globe.adsbexchange.com/?icao={flight['hex']}

---
This alert was generated by the Air France Squawk 7700 Monitor.
"""
    
    try:
        msg = MIMEMultipart()
        msg['From'] = config["address"]
        msg['To'] = config["address"]
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(config["smtp_server"], config["smtp_port"]) as server:
            server.starttls()
            server.login(config["address"], config["password"])
            server.send_message(msg)
        
        print(f"Email notification sent for flight {flight['flight']}")
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def main():
    print(f"Checking for Air France squawk 7700 at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    # Get email configuration
    email_config = get_email_config()
    
    # Load previous state
    state = load_previous_state()
    
    # Fetch current squawk 7700 flights
    af_flights = fetch_squawk_7700_flights()
    
    if not af_flights:
        print("No Air France flights currently squawking 7700.")
        # Clear old alerts after some time
        state["alerted_flights"] = []
        save_state(state)
        return
    
    print(f"Found {len(af_flights)} Air France flight(s) with squawk 7700!")
    
    # Process each flight
    new_alerts = []
    for flight in af_flights:
        flight_hash = get_flight_hash(flight)
        
        if flight_hash not in state["alerted_flights"]:
            print(f"New emergency: {flight['flight']}")
            send_email_notification(flight, email_config)
            new_alerts.append(flight_hash)
        else:
            print(f"Already alerted for flight {flight['flight']}")
    
    # Update state
    state["alerted_flights"].extend(new_alerts)
    save_state(state)
    
    print("Check complete.")


if __name__ == "__main__":
    main()
