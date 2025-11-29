# Air France Squawk 7700 Monitor

Automated monitoring system that sends email alerts when Air France flights declare a general emergency (squawk 7700).

## What is Squawk 7700?

Squawk 7700 is the international transponder code for a general emergency. When a pilot enters this code, it alerts air traffic control that the aircraft is experiencing an emergency situation.

## Features

- Monitors live flight data every 5 minutes using ADS-B Exchange
- Filters specifically for Air France (AF/AFR) flights
- Sends detailed email notifications with:
  - Flight number and registration
  - Aircraft type
  - Current position (altitude, coordinates, speed)
  - Route information (origin/destination)
  - Direct link to track the flight live
- Prevents duplicate alerts for the same emergency
- Can be manually triggered via GitHub Actions

## Setup Instructions

### 1. Fork or Clone this Repository

```bash
git clone https://github.com/mave330/squawk.git
```

### 2. Configure Repository Secrets

Go to your repository **Settings** > **Secrets and variables** > **Actions** and add the following secrets:

| Secret Name | Description | Example |
|-------------|-------------|--------|
| `EMAIL_ADDRESS` | Your email address (sender and recipient) | `your.email@gmail.com` |
| `EMAIL_PASSWORD` | App password (not your regular password) | `xxxx xxxx xxxx xxxx` |
| `SMTP_SERVER` | SMTP server address | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |

### 3. Gmail App Password Setup

If using Gmail:

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Step Verification if not already enabled
3. Go to **App passwords**
4. Create a new app password for "Mail"
5. Use this 16-character password as `EMAIL_PASSWORD`

### 4. Enable GitHub Actions

The workflow runs automatically every 5 minutes. You can also:

1. Go to **Actions** tab
2. Select "Air France Squawk 7700 Monitor"
3. Click **Run workflow** to test manually

## How It Works

1. **Data Source**: The script fetches live squawk 7700 data from ADS-B Exchange's public endpoint
2. **Filtering**: It filters the data for flights with callsigns starting with "AF" or "AFR"
3. **Deduplication**: Previously alerted flights are tracked to avoid spam
4. **Notification**: When a new Air France emergency is detected, an email is sent

## Email Notification Example

```
Subject: ALERT: Air France AF1234 - SQUAWK 7700 EMERGENCY

AIR FRANCE EMERGENCY ALERT
==========================

An Air France flight is currently squawking 7700 (General Emergency).

Flight Details:
---------------
Flight Number: AF1234
Registration: F-GKXS
Aircraft Type: A320
Squawk Code: 7700

Position Information:
--------------------
Altitude: 35000 ft
Ground Speed: 450 kts
Latitude: 48.8566
Longitude: 2.3522

Track live at:
https://globe.adsbexchange.com/?icao=XXXXXX
```

## File Structure

```
squawk/
|-- .github/
|   |-- workflows/
|       |-- squawk_monitor.yml    # GitHub Actions workflow
|-- scripts/
|   |-- check_squawk.py           # Main monitoring script
|-- README.md                      # This file
```

## Limitations

- Depends on ADS-B Exchange data availability
- 5-minute polling interval (GitHub Actions limitation)
- Requires aircraft to be within ADS-B coverage
- Some flights may not broadcast callsign

## License

MIT License - Feel free to modify and use for your own monitoring needs.

## Disclaimer

This tool is for informational purposes only. Emergency situations are handled by professional aviation authorities. Do not interfere with emergency operations.
