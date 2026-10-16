"""
data_loader.py
--------------
Loads climate data from either:
  1. the simulated raw CSV (default), or
  2. a REAL public dataset in data/external/ (e.g. NASA POWER, Kaggle
     "Daily Delhi Climate", IMD gridded exports), mapped to our schema.

Standard schema used by the whole project:
    date | city | temp_mean | temp_max | temp_min | rainfall_mm | humidity_pct
"""

from pathlib import Path

import pandas as pd

from src import config
from src.utils import get_logger

logger = get_logger(__name__)

REQUIRED_COLUMNS = ["date", "city", "temp_mean", "temp_max", "temp_min",
                    "rainfall_mm", "humidity_pct"]


def load_raw_data(path: Path = config.RAW_DATA_FILE) -> pd.DataFrame:
    """Load the raw CSV and validate that the expected columns exist."""
    if not Path(path).exists():
        raise FileNotFoundError(
            f"{path} not found. Run `python main.py --step generate` first.")
    df = pd.read_csv(path)
    validate_schema(df)
    logger.info("Loaded %d rows x %d columns from %s", *df.shape, Path(path).name)
    return df


def validate_schema(df: pd.DataFrame) -> None:
    """Fail early with a helpful message if columns are missing."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}. "
                         f"Found: {list(df.columns)}")


def load_external_csv(path: Path, column_map: dict, city: str | None = None) -> pd.DataFrame:
    """
    Load a real public CSV and rename its columns to our schema.

    Example - Kaggle 'Daily Delhi Climate' (columns: date, meantemp,
    humidity, wind_speed, meanpressure):

        df = load_external_csv(
            "data/external/DailyDelhiClimateTrain.csv",
            column_map={"date": "date", "meantemp": "temp_mean",
                        "humidity": "humidity_pct"},
            city="Delhi")

    Columns the source does not provide are filled with NaN, so the rest of
    the pipeline still runs (those charts will simply be empty).
    """
    df = pd.read_csv(path).rename(columns=column_map)
    if city is not None:
        df["city"] = city
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    return df[REQUIRED_COLUMNS]
