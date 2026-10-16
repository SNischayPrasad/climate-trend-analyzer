"""
Unit tests for the Climate Trend Analyzer.
Run with:  pytest -v
"""

import numpy as np
import pandas as pd
import pytest

from src import config
from src.anomaly_detection import detect_temperature_anomalies, group_into_events
from src.data_generator import _ar1_noise, _simulate_city
from src.feature_engineering import add_features
from src.preprocessing import clean_data
from src.trend_analysis import analyze_series, mann_kendall


@pytest.fixture(scope="module")
def small_raw():
    """Two years of simulated data for one city, with some broken values."""
    rng = np.random.default_rng(0)
    dates = pd.date_range("2000-01-01", "2001-12-31", freq="D")
    df, _ = _simulate_city("Delhi", config.CITY_PROFILES["Delhi"], dates, rng)
    df = df.copy()
    df.loc[5, "temp_mean"] = -999          # sensor error
    df.loc[10, "humidity_pct"] = np.nan    # missing value
    df.loc[20, "rainfall_mm"] = 5000       # impossible rainfall
    df = pd.concat([df, df.iloc[:3]])      # duplicates
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    return df


def test_simulation_shape_and_ranges():
    rng = np.random.default_rng(1)
    dates = pd.date_range("2000-01-01", "2004-12-31", freq="D")
    df, events = _simulate_city("Mumbai", config.CITY_PROFILES["Mumbai"], dates, rng)
    assert len(df) == len(dates)
    assert (df["rainfall_mm"] >= 0).all()
    assert df["humidity_pct"].between(0, 100).all()
    assert (df["temp_max"] >= df["temp_min"]).all()
    assert len(events) > 0


def test_ar1_noise_is_autocorrelated():
    x = _ar1_noise(5000, phi=0.7, sigma=1.0, rng=np.random.default_rng(2))
    lag1 = np.corrcoef(x[:-1], x[1:])[0, 1]
    assert 0.6 < lag1 < 0.8


def test_cleaning_removes_errors_and_duplicates(small_raw):
    clean = clean_data(small_raw, save=False)
    assert clean.duplicated(subset=["city", "date"]).sum() == 0
    assert clean[["temp_mean", "humidity_pct", "rainfall_mm"]].isna().sum().sum() == 0
    assert clean["temp_mean"].min() > -50                 # -999 sentinel gone
    assert clean["rainfall_mm"].max() < 1000              # impossible value gone
    assert len(clean) == 731                              # complete daily calendar


def test_mann_kendall_detects_trend():
    rng = np.random.default_rng(3)
    years = np.arange(1990, 2025)
    up = 25 + 0.03 * (years - 1990) + rng.normal(0, 0.15, len(years))
    flat = 25 + rng.normal(0, 0.15, len(years))
    assert mann_kendall(up)["trend"] == "increasing"
    assert mann_kendall(-up)["trend"] == "decreasing"
    assert mann_kendall(flat)["p_value"] > 0.01


def test_sen_slope_recovers_true_slope():
    years = np.arange(1990, 2025)
    values = 20 + 0.025 * (years - 1990)
    res = analyze_series(years, values)
    assert res["sen_slope_per_decade"] == pytest.approx(0.25, abs=1e-6)


def test_anomaly_detection_finds_injected_spike(small_raw):
    clean = clean_data(small_raw, save=False)
    clean.loc[clean["date"] == "2001-03-10", "temp_mean"] += 15   # obvious heat spike
    feats = detect_temperature_anomalies(add_features(clean))
    events = group_into_events(feats)
    hit = events[(events.start_date <= "2001-03-10") & (events.end_date >= "2001-03-10")]
    assert len(hit) == 1
    assert hit.iloc[0]["type"] == "hot_anomaly"
