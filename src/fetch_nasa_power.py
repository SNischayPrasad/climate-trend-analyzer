"""
fetch_nasa_power.py  (OPTIONAL - real public data)
--------------------------------------------------
Downloads REAL daily climate data from NASA POWER (free, no API key):
https://power.larc.nasa.gov/

It saves a CSV in our standard schema to data/external/, which you can then
analyse with:

    python main.py --step all --source external --input data/external/nasa_power_india.csv

Usage:
    python -m src.fetch_nasa_power --start 1990 --end 2024
"""

import argparse

import pandas as pd
import requests

from src import config
from src.utils import get_logger

logger = get_logger(__name__)

API_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

# Approximate city-centre coordinates
CITY_COORDS = {
    "Delhi": (28.61, 77.21),
    "Mumbai": (19.08, 72.88),
    "Chennai": (13.08, 80.27),
    "Bengaluru": (12.97, 77.59),
}

# NASA parameter code -> our column name
PARAMS = {
    "T2M": "temp_mean",          # temperature at 2 m (deg C)
    "T2M_MAX": "temp_max",
    "T2M_MIN": "temp_min",
    "PRECTOTCORR": "rainfall_mm",  # corrected precipitation (mm/day)
    "RH2M": "humidity_pct",      # relative humidity at 2 m (%)
}


def fetch_city(city: str, lat: float, lon: float, start: int, end: int) -> pd.DataFrame:
    """Download one city and return it in our schema."""
    query = {
        "parameters": ",".join(PARAMS),
        "community": "AG",
        "latitude": lat,
        "longitude": lon,
        "start": f"{start}0101",
        "end": f"{end}1231",
        "format": "JSON",
    }
    logger.info("Requesting NASA POWER data for %s ...", city)
    resp = requests.get(API_URL, params=query, timeout=120)
    resp.raise_for_status()
    data = resp.json()["properties"]["parameter"]

    df = pd.DataFrame({PARAMS[k]: pd.Series(v) for k, v in data.items()})
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df = df.replace(-999.0, pd.NA)          # NASA's missing-value code
    df = df.rename_axis("date").reset_index()
    df["city"] = city
    return df


def main():
    parser = argparse.ArgumentParser(description="Download NASA POWER climate data")
    parser.add_argument("--start", type=int, default=1990)
    parser.add_argument("--end", type=int, default=2024)
    args = parser.parse_args()

    config.ensure_dirs()
    frames = [fetch_city(c, lat, lon, args.start, args.end)
              for c, (lat, lon) in CITY_COORDS.items()]
    out = pd.concat(frames, ignore_index=True)
    cols = ["date", "city", "temp_mean", "temp_max", "temp_min", "rainfall_mm", "humidity_pct"]
    path = config.EXTERNAL_DIR / "nasa_power_india.csv"
    out[cols].to_csv(path, index=False)
    logger.info("Saved %d rows -> %s", len(out), path)


if __name__ == "__main__":
    main()
