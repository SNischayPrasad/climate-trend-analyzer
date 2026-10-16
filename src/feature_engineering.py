"""
feature_engineering.py
----------------------
Creates the variables that climate analysts actually reason with:

Calendar features : year, month, day_of_year, decade, season (IMD seasons)
Climatology       : 1991-2020 "normal" temperature for each city & day of year
Anomalies         : temp_anomaly  = observed - normal          (for reporting)
                    temp_residual = anomaly - long-term trend  (for detection)
                    temp_zscore   = residual / typical variability
Indicators        : hot_day, cold_night, rainy_day, heavy_rain_day,
                    diurnal_range, 7-day & 30-day rolling means
Aggregates        : monthly and yearly tables per city
"""

import numpy as np
import pandas as pd

from src import config
from src.utils import get_logger

logger = get_logger(__name__)

# India Meteorological Department (IMD) seasons
SEASON_MAP = {12: "Winter", 1: "Winter", 2: "Winter",
              3: "Pre-Monsoon", 4: "Pre-Monsoon", 5: "Pre-Monsoon",
              6: "Monsoon", 7: "Monsoon", 8: "Monsoon", 9: "Monsoon",
              10: "Post-Monsoon", 11: "Post-Monsoon"}
SEASON_ORDER = ["Winter", "Pre-Monsoon", "Monsoon", "Post-Monsoon"]


def _smooth_circular(values: pd.Series, window: int = 31) -> pd.Series:
    """Rolling mean over day-of-year that wraps Dec 31 -> Jan 1."""
    pad = window // 2
    extended = pd.concat([values.iloc[-pad:], values, values.iloc[:pad]])
    smoothed = extended.rolling(window, center=True).mean()
    return smoothed.iloc[pad:-pad]


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add calendar, climatology, anomaly and indicator features."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day_of_year"] = df["date"].dt.dayofyear.clip(upper=365)   # fold leap day
    df["decade"] = (df["year"] // 10 * 10).astype(str) + "s"
    df["season"] = df["month"].map(SEASON_MAP)
    df["diurnal_range"] = df["temp_max"] - df["temp_min"]
    df["rainy_day"] = (df["rainfall_mm"] >= 2.5).astype(int)        # IMD definition
    df["heavy_rain_day"] = (df["rainfall_mm"] >= 64.5).astype(int)  # IMD 'heavy rain'

    frames = []
    for city, g in df.groupby("city"):
        g = g.sort_values("date").copy()
        base = g[(g["year"] >= config.BASELINE_START) & (g["year"] <= config.BASELINE_END)]

        # --- Climatological normal for each day of year (smoothed) ---
        clim = base.groupby("day_of_year")["temp_mean"].mean().reindex(range(1, 366))
        clim = _smooth_circular(clim.interpolate())
        g["temp_normal"] = g["day_of_year"].map(clim)
        g["temp_anomaly"] = g["temp_mean"] - g["temp_normal"]

        # --- Remove long-term trend so detection is fair across decades ---
        t = (g["date"] - g["date"].min()).dt.days.values
        slope, intercept = np.polyfit(t, g["temp_anomaly"].values, 1)
        g["temp_residual"] = g["temp_anomaly"] - (slope * t + intercept)
        month_std = g.groupby("month")["temp_residual"].transform("std")
        g["temp_zscore"] = g["temp_residual"] / month_std

        # --- Extreme-heat indicators relative to the baseline climate ---
        tmax_p90 = base.groupby("month")["temp_max"].quantile(0.90)
        tmin_p10 = base.groupby("month")["temp_min"].quantile(0.10)
        g["hot_day"] = (g["temp_max"] > g["month"].map(tmax_p90)).astype(int)
        g["cold_night"] = (g["temp_min"] < g["month"].map(tmin_p10)).astype(int)

        # --- Rolling windows smooth day-to-day weather noise ---
        g["temp_7d_avg"] = g["temp_mean"].rolling(7, min_periods=1).mean()
        g["rain_30d_total"] = g["rainfall_mm"].rolling(30, min_periods=1).sum()
        frames.append(g)

    out = pd.concat(frames, ignore_index=True)
    logger.info("Engineered %d columns for %d rows", out.shape[1], len(out))
    return out


def build_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly aggregates per city (input for forecasting & Isolation Forest)."""
    monthly = (df.set_index("date").groupby("city")
               .resample("MS")
               .agg({"temp_mean": "mean", "temp_max": "max", "temp_min": "min",
                     "rainfall_mm": "sum", "humidity_pct": "mean",
                     "temp_anomaly": "mean", "rainy_day": "sum", "hot_day": "sum"})
               .reset_index())
    monthly["year"] = monthly["date"].dt.year
    monthly["month"] = monthly["date"].dt.month
    return monthly


def build_yearly(df: pd.DataFrame) -> pd.DataFrame:
    """Yearly aggregates per city (input for long-term trend tests)."""
    yearly = (df.groupby(["city", "year"])
              .agg(temp_mean=("temp_mean", "mean"),
                   temp_max_avg=("temp_max", "mean"),
                   temp_min_avg=("temp_min", "mean"),
                   temp_anomaly=("temp_anomaly", "mean"),
                   rainfall_total=("rainfall_mm", "sum"),
                   rainy_days=("rainy_day", "sum"),
                   heavy_rain_days=("heavy_rain_day", "sum"),
                   max_1day_rain=("rainfall_mm", "max"),
                   hot_days=("hot_day", "sum"),
                   cold_nights=("cold_night", "sum"),
                   humidity_mean=("humidity_pct", "mean"))
              .reset_index())
    return yearly


def run_feature_engineering(clean: pd.DataFrame, save: bool = True):
    """Create daily features + monthly + yearly tables and save them."""
    feats = add_features(clean)
    monthly = build_monthly(feats)
    yearly = build_yearly(feats)
    if save:
        feats.to_csv(config.FEATURES_FILE, index=False)
        monthly.to_csv(config.MONTHLY_FILE, index=False)
        yearly.to_csv(config.YEARLY_FILE, index=False)
        logger.info("Saved features, monthly (%d rows) and yearly (%d rows) tables",
                    len(monthly), len(yearly))
    return feats, monthly, yearly
