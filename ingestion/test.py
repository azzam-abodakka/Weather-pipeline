import time

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

URL = "https://api.open-meteo.com/v1/forecast"
HOURLY_PARAMS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
]

germany_states = {
    "Baden-Württemberg": {"city": "Stuttgart", "lat": 48.78, "lon": 9.18},
    "Bavaria": {"city": "Munich", "lat": 48.14, "lon": 11.58},
    "Berlin": {"city": "Berlin", "lat": 52.52, "lon": 13.40},
    "Brandenburg": {"city": "Potsdam", "lat": 52.40, "lon": 13.06},
    "Bremen": {"city": "Bremen", "lat": 53.07, "lon": 8.80},
    "Hamburg": {"city": "Hamburg", "lat": 53.55, "lon": 9.99},
    "Hesse": {"city": "Wiesbaden", "lat": 50.08, "lon": 8.24},
    "Lower Saxony": {"city": "Hanover", "lat": 52.37, "lon": 9.73},
    "Mecklenburg-Vorpommern": {"city": "Schwerin", "lat": 53.63, "lon": 11.41},
    "North Rhine-Westphalia": {"city": "Düsseldorf", "lat": 51.22, "lon": 6.77},
    "Rhineland-Palatinate": {"city": "Mainz", "lat": 50.00, "lon": 8.27},
    "Saarland": {"city": "Saarbrücken", "lat": 49.24, "lon": 6.99},
    "Saxony": {"city": "Dresden", "lat": 51.05, "lon": 13.73},
    "Saxony-Anhalt": {"city": "Magdeburg", "lat": 52.12, "lon": 11.63},
    "Schleswig-Holstein": {"city": "Kiel", "lat": 54.32, "lon": 10.13},
    "Thuringia": {"city": "Erfurt", "lat": 50.98, "lon": 11.03},
}

# Session with automatic retries
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

all_dfs = []
failed = []

for state_name, info in germany_states.items():
    params = {
        "latitude": info["lat"],
        "longitude": info["lon"],
        "hourly": ",".join(HOURLY_PARAMS),
        "timezone": "Europe/Berlin",
    }

    print(f"Fetching weather for {state_name} ({info['city']})...")

    try:
        response = session.get(url=URL, params=params, timeout=15)
        response.raise_for_status()

        df = pd.DataFrame(response.json()["hourly"])
        df.insert(0, "city", info["city"])
        df.insert(0, "state", state_name)
        all_dfs.append(df)

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch {state_name}: {e}")
        failed.append(state_name)

    # Pause between requests to avoid rate limits
    time.sleep(0.5)

print("Failed states:", failed)

if all_dfs:
    master_df = pd.concat(all_dfs, ignore_index=True)
    master_df["time"] = pd.to_datetime(master_df["time"])
    master_df.to_csv("data/weather_raw.csv", index=False)
    print(master_df.dtypes)
    print(master_df.isna().sum())
    print("\nSuccess! Master dataset shape:", master_df.shape)
else:
    print("\nAll requests failed. Check your internet connection or VPN.")