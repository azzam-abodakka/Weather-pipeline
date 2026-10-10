import logging
from pathlib import Path

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

URL = "https://api.open-meteo.com/v1/forecast"
HOURLY_VARS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
]

# state: (capital, latitude, longitude)
STATES = {
    "Baden-Württemberg": ("Stuttgart", 48.78, 9.18),
    "Bayern": ("München", 48.14, 11.58),
    "Berlin": ("Berlin", 52.52, 13.41),
    "Brandenburg": ("Potsdam", 52.40, 13.07),
    "Bremen": ("Bremen", 53.08, 8.80),
    "Hamburg": ("Hamburg", 53.55, 9.99),
    "Hessen": ("Wiesbaden", 50.08, 8.24),
    "Mecklenburg-Vorpommern": ("Schwerin", 53.63, 11.41),
    "Niedersachsen": ("Hannover", 52.37, 9.74),
    "Nordrhein-Westfalen": ("Düsseldorf", 51.23, 6.78),
    "Rheinland-Pfalz": ("Mainz", 50.00, 8.27),
    "Saarland": ("Saarbrücken", 49.24, 7.00),
    "Sachsen": ("Dresden", 51.05, 13.74),
    "Sachsen-Anhalt": ("Magdeburg", 52.13, 11.63),
    "Schleswig-Holstein": ("Kiel", 54.32, 10.14),
    "Thüringen": ("Erfurt", 50.98, 11.03),
}


def fetch_city(lat: float, lon: float) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(HOURLY_VARS),
        "timezone": "Europe/Berlin",
        "forecast_days": 3,
    }
    r = requests.get(URL, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def to_dataframe(state: str, city: str, payload: dict) -> pd.DataFrame:
    df = pd.DataFrame(payload["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    df.insert(0, "city", city)
    df.insert(0, "state", state)
    return df


def show_raw_structure(payload: dict) -> None:
    print("\n=== RAW JSON STRUCTURE (first city) ===")
    print("top-level keys:", list(payload.keys()))
    print("hourly_units:", payload.get("hourly_units"))
    for key, values in payload["hourly"].items():
        print(f"  hourly[{key!r}]: {len(values)} values, first = {values[0]}")


def show_table_structure(df: pd.DataFrame) -> None:
    print("\n=== TABLE STRUCTURE ===")
    print("shape (rows, columns):", df.shape)
    print("\ncolumns and types:")
    print(df.dtypes)
    print("\nfirst rows:")
    print(df.head())
    print("\nmissing values per column:")
    print(df.isna().sum())
    print("\nrows per state:")
    print(df["state"].value_counts())
    print("\nnumeric summary:")
    print(df.describe())


def main() -> None:
    frames = []
    first_payload = None

    for state, (city, lat, lon) in STATES.items():
        try:
            payload = fetch_city(lat, lon)
        except requests.RequestException as e:
            logging.error("failed for %s (%s): %s", city, state, e)
            continue
        if first_payload is None:
            first_payload = payload
        frames.append(to_dataframe(state, city, payload))
        logging.info("fetched %s", city)

    if not frames:
        logging.error("no data fetched")
        return

    df = pd.concat(frames, ignore_index=True)
    show_raw_structure(first_payload)
    show_table_structure(df)

    out = Path("data/weather_raw.csv")
    df.to_csv(out, index=False)
    logging.info("saved %d rows to %s", len(df), out)


if __name__ == "__main__":
    main()