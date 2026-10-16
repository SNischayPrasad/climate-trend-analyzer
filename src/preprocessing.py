"""
preprocessing.py
----------------
Data cleaning module. Turns messy raw sensor data into an analysis-ready
table, and writes a data-quality report so every decision is auditable.

Cleaning steps (in order):
    1. Parse dates and drop rows with unparseable dates
    2. Remove exact duplicate rows, then duplicate (city, date) records
    3. Replace sentinel error codes (-999 / 999) with NaN
    4. Flag physically impossible values (range checks) as NaN
    5. Fix logical inconsistencies (temp_min > temp_max)
    6. Re-index each city to a complete daily calendar (exposes gaps)
    7. Fill short gaps by time interpolation (temperature, humidity);
       rainfall gaps are filled with 0 only for 1-day gaps, else left NaN
       and then filled by the day-of-year median (climatology).
"""

import numpy as np
import pandas as pd

from src import config
from src.utils import get_logger, save_table

logger = get_logger(__name__)

NUMERIC_COLS = ["temp_mean", "temp_max", "temp_min", "rainfall_mm", "humidity_pct"]

# Physically plausible ranges for Indian cities (anything outside = error)
VALID_RANGES = {
    "temp_mean": (-10, 50),
    "temp_max": (-5, 55),
    "temp_min": (-15, 45),
    "rainfall_mm": (0, 1000),
    "humidity_pct": (0, 100),
}

MAX_INTERPOLATION_GAP = 7    # days


def clean_data(raw: pd.DataFrame, save: bool = True) -> pd.DataFrame:
    """Run the full cleaning pipeline and return the clean DataFrame."""
    df = raw.copy()
    report = [("raw_rows", len(df))]
    report.append(("raw_missing_cells", int(df[NUMERIC_COLS].isna().sum().sum())))

    # 1) Dates -----------------------------------------------------------
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    bad_dates = int(df["date"].isna().sum())
    df = df.dropna(subset=["date"])
    report.append(("unparseable_dates_dropped", bad_dates))

    # 2) Duplicates -------------------------------------------------------
    before = len(df)
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset=["city", "date"], keep="first")
    report.append(("duplicate_rows_removed", before - len(df)))

    # 3) Sentinel values ---------------------------------------------------
    sentinel_mask = df[NUMERIC_COLS].isin([-999, 999, -9999, 9999])
    report.append(("sentinel_values_replaced", int(sentinel_mask.sum().sum())))
    df[NUMERIC_COLS] = df[NUMERIC_COLS].mask(sentinel_mask)

    # 4) Range checks ------------------------------------------------------
    out_of_range = 0
    for col, (lo, hi) in VALID_RANGES.items():
        bad = (df[col] < lo) | (df[col] > hi)
        out_of_range += int(bad.sum())
        df.loc[bad, col] = np.nan
    report.append(("out_of_range_values_removed", out_of_range))

    # 5) Logical consistency: min must not exceed max ------------------------
    swapped = df["temp_min"] > df["temp_max"]
    df.loc[swapped, ["temp_min", "temp_max"]] = df.loc[swapped, ["temp_max", "temp_min"]].values
    report.append(("min_max_swaps", int(swapped.sum())))

    # 6) Complete daily calendar per city ------------------------------------
    frames = []
    for city, g in df.groupby("city"):
        full_idx = pd.date_range(g["date"].min(), g["date"].max(), freq="D")
        g = g.set_index("date").reindex(full_idx)
        g.index.name = "date"
        g["city"] = city
        frames.append(g)
    df = pd.concat(frames)
    report.append(("missing_cells_before_imputation", int(df[NUMERIC_COLS].isna().sum().sum())))

    # 7) Imputation ---------------------------------------------------------
    df = pd.concat([_impute_city(g) for _, g in df.groupby("city")])
    report.append(("missing_cells_after_imputation", int(df[NUMERIC_COLS].isna().sum().sum())))

    df = df.reset_index().sort_values(["city", "date"]).reset_index(drop=True)
    df[NUMERIC_COLS] = df[NUMERIC_COLS].round(2)
    report.append(("clean_rows", len(df)))

    report_df = pd.DataFrame(report, columns=["check", "value"])
    for check, value in report:
        logger.info("  %-35s %s", check, value)

    if save:
        df.to_csv(config.CLEAN_DATA_FILE, index=False)
        save_table(report_df, "data_quality_report.csv")
        save_table(_missing_by_column(raw), "missing_values_by_column.csv")
        logger.info("Saved clean data -> %s", config.rel(config.CLEAN_DATA_FILE))
    return df


def _impute_city(g: pd.DataFrame) -> pd.DataFrame:
    """Fill gaps for one city."""
    g = g.copy()
    # Temperatures & humidity change smoothly -> time interpolation for short gaps
    for col in ["temp_mean", "temp_max", "temp_min", "humidity_pct"]:
        g[col] = g[col].interpolate(method="time", limit=MAX_INTERPOLATION_GAP,
                                    limit_direction="both")
    # Rainfall is intermittent: interpolation would invent drizzle.
    # Use the median for that day-of-year (climatology) instead.
    doy = g.index.dayofyear
    for col in NUMERIC_COLS:
        if g[col].isna().any():
            clim = g.groupby(doy)[col].transform("median")
            g[col] = g[col].fillna(clim)
    return g


def _missing_by_column(raw: pd.DataFrame) -> pd.DataFrame:
    """Missing + sentinel counts per column in the RAW data (for the EDA chart)."""
    rows = []
    for col in NUMERIC_COLS:
        rows.append({
            "column": col,
            "missing": int(raw[col].isna().sum()),
            "sentinel_errors": int(raw[col].isin([-999, 999]).sum()),
            "missing_pct": round(raw[col].isna().mean() * 100, 2),
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    from src.data_loader import load_raw_data
    clean_data(load_raw_data())
