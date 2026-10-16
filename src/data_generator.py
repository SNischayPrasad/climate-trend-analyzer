"""
data_generator.py
-----------------
VIRTUAL SIMULATION of 35 years of daily climate data for four Indian cities.

Why simulate?
    Students rarely have access to institutional climate databases. A
    physically-motivated simulation lets us build and test the *entire*
    analysis pipeline, and - unlike real data - we KNOW the true answer
    (the injected warming trend and extreme events), so we can measure how
    well our trend and anomaly methods recover it.

How each variable is built
    temperature = baseline + seasonal cycle + long-term warming
                  + autocorrelated weather noise + injected extreme events
    rainfall    = (does it rain today? -> Bernoulli with monsoon-shaped
                  probability) x (how much? -> Gamma distribution)
                  + injected cloudburst / extreme-rain days
    humidity    = seasonal level + extra moisture on rainy days
                  - drying on unusually hot days + noise

Finally, realistic data-quality problems (missing values, -999 sensor
errors, duplicate rows) are injected so the cleaning module has real work.
"""

import numpy as np
import pandas as pd

from src import config
from src.utils import get_logger

logger = get_logger(__name__)


def _circular_gaussian(doy: np.ndarray, peak: int, width: float) -> np.ndarray:
    """Bell-shaped curve over the year that wraps around Dec -> Jan."""
    dist = np.abs(doy - peak)
    dist = np.minimum(dist, 365.25 - dist)          # wrap-around distance
    return np.exp(-0.5 * (dist / width) ** 2)


def _ar1_noise(n: int, phi: float, sigma: float, rng: np.random.Generator) -> np.ndarray:
    """
    AR(1) 'red' noise: today's weather depends partly on yesterday's.
    x[t] = phi * x[t-1] + e[t]. Real weather is persistent, so pure white
    noise would look unrealistic.
    """
    eps = rng.normal(0, sigma * np.sqrt(1 - phi ** 2), n)
    x = np.empty(n)
    x[0] = eps[0]
    for t in range(1, n):
        x[t] = phi * x[t - 1] + eps[t]
    return x


def _simulate_city(city: str, profile: dict, dates: pd.DatetimeIndex,
                   rng: np.random.Generator):
    """Simulate one city. Returns (dataframe, list_of_injected_events)."""
    n = len(dates)
    doy = dates.dayofyear.values.astype(float)
    years_elapsed = (dates - dates[0]).days.values / 365.25

    # ---------------- Temperature ----------------
    seasonal = profile["temp_amplitude"] * np.cos(
        2 * np.pi * (doy - profile["peak_day"]) / 365.25)
    trend = profile["warming_per_decade"] / 10 * years_elapsed
    noise_sigma = 0.6 + 0.12 * profile["temp_amplitude"]   # continental = noisier
    noise = _ar1_noise(n, phi=0.7, sigma=noise_sigma, rng=rng)
    temp_mean = profile["temp_mean"] + seasonal + trend + noise

    # ---------------- Rainfall ----------------
    monsoon = _circular_gaussian(doy, profile["monsoon_peak_day"], profile["monsoon_width"])
    wet_prob = 0.04 + 0.78 * monsoon                       # chance of rain today
    shape = 0.75
    scale = profile["rain_annual_mm"] / (shape * wet_prob[:365].sum())
    intensity_trend = 1 + 0.015 * years_elapsed / 10       # +1.5 % intensity / decade
    is_wet = rng.random(n) < wet_prob
    rainfall = np.where(is_wet, rng.gamma(shape, scale, n) * intensity_trend, 0.0)

    # ---------------- Inject extreme events (ground truth) ----------------
    events = []
    years = np.unique(dates.year)

    def random_start(center_doy, spread):
        year = rng.choice(years)
        day = int((center_doy + rng.integers(-spread, spread)) % 365) + 1
        return pd.Timestamp(year=year, month=1, day=1) + pd.Timedelta(days=day - 1)

    for _ in range(config.N_HEATWAVES_PER_CITY):
        start = random_start(profile["peak_day"], 35)
        length = int(rng.integers(3, 8))
        magnitude = float(rng.uniform(5.5, 8.0))
        idx = np.where((dates >= start) & (dates < start + pd.Timedelta(days=length)))[0]
        temp_mean[idx] += magnitude
        rainfall[idx] = 0.0                                  # heatwaves are dry
        events.append(dict(city=city, event_type="heatwave", start_date=start.date(),
                           end_date=(start + pd.Timedelta(days=length - 1)).date(),
                           magnitude=round(magnitude, 2), unit="degC"))

    for _ in range(config.N_COLD_SPELLS_PER_CITY):
        start = random_start(profile["peak_day"] + 182, 30)
        length = int(rng.integers(3, 7))
        magnitude = float(rng.uniform(5.0, 7.0))
        idx = np.where((dates >= start) & (dates < start + pd.Timedelta(days=length)))[0]
        temp_mean[idx] -= magnitude
        events.append(dict(city=city, event_type="cold_spell", start_date=start.date(),
                           end_date=(start + pd.Timedelta(days=length - 1)).date(),
                           magnitude=round(-magnitude, 2), unit="degC"))

    for _ in range(config.N_EXTREME_RAIN_PER_CITY):
        day = random_start(profile["monsoon_peak_day"], 30)
        amount = float(rng.uniform(0.12, 0.25) * profile["rain_annual_mm"])
        idx = np.where(dates == day)[0]
        rainfall[idx] = amount
        events.append(dict(city=city, event_type="extreme_rain", start_date=day.date(),
                           end_date=day.date(), magnitude=round(amount, 1), unit="mm"))

    # ---------------- Max / Min temperature ----------------
    # Diurnal range is wider in dry season and narrower on rainy days.
    diurnal = 8 + 4 * (1 - monsoon) - 3 * (rainfall > 5) + rng.normal(0, 0.8, n)
    diurnal = np.clip(diurnal, 3, 16)
    temp_max = temp_mean + diurnal / 2
    temp_min = temp_mean - diurnal / 2

    # ---------------- Humidity ----------------
    temp_anom = temp_mean - (profile["temp_mean"] + seasonal + trend)
    humidity = (profile["humidity_mean"] + 18 * (monsoon - monsoon.mean())
                + 8 * (rainfall > 0) - 1.2 * temp_anom + rng.normal(0, 4, n))
    humidity = np.clip(humidity, 8, 100)

    df = pd.DataFrame({
        "date": dates,
        "city": city,
        "temp_mean": temp_mean.round(2),
        "temp_max": temp_max.round(2),
        "temp_min": temp_min.round(2),
        "rainfall_mm": rainfall.round(1),
        "humidity_pct": humidity.round(1),
    })
    return df, events


def _inject_data_quality_issues(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Make the clean simulation look like messy real-world sensor data."""
    df = df.copy()
    numeric_cols = ["temp_mean", "temp_max", "temp_min", "rainfall_mm", "humidity_pct"]
    n = len(df)

    # 1) Random missing values (sensor outages, transmission failures)
    for col in numeric_cols:
        mask = rng.random(n) < config.MISSING_RATE
        df.loc[mask, col] = np.nan

    # 2) Sentinel error codes (-999 / 999) that some stations log on failure
    for col in numeric_cols:
        mask = rng.random(n) < config.SENSOR_ERROR_RATE
        df.loc[mask, col] = rng.choice([-999.0, 999.0], mask.sum())

    # 3) A short block outage: one city loses 20 consecutive days
    outage_start = int(rng.integers(0, n - 20))
    df.loc[outage_start:outage_start + 19, numeric_cols] = np.nan

    # 4) Duplicate rows (double uploads)
    dupes = df.sample(config.DUPLICATE_ROWS, random_state=config.RANDOM_SEED)
    df = pd.concat([df, dupes], ignore_index=True)

    # 5) Shuffle row order, as merged files often arrive unsorted
    df = df.sample(frac=1, random_state=config.RANDOM_SEED).reset_index(drop=True)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    return df


def generate_climate_data(save: bool = True) -> pd.DataFrame:
    """Simulate all cities, inject quality issues, and save raw CSVs."""
    config.ensure_dirs()
    rng = np.random.default_rng(config.RANDOM_SEED)
    dates = pd.date_range(config.START_DATE, config.END_DATE, freq="D")

    frames, all_events = [], []
    for city, profile in config.CITY_PROFILES.items():
        logger.info("Simulating %s (%d days)...", city, len(dates))
        df_city, events = _simulate_city(city, profile, dates, rng)
        frames.append(df_city)
        all_events.extend(events)

    clean_sim = pd.concat(frames, ignore_index=True)
    raw = _inject_data_quality_issues(clean_sim, rng)
    events_df = pd.DataFrame(all_events).sort_values(["city", "start_date"])

    if save:
        raw.to_csv(config.RAW_DATA_FILE, index=False)
        events_df.to_csv(config.INJECTED_EVENTS_FILE, index=False)
        logger.info("Saved raw data -> %s (%d rows)", config.rel(config.RAW_DATA_FILE), len(raw))
        logger.info("Saved ground-truth events -> %s (%d events)",
                    config.rel(config.INJECTED_EVENTS_FILE), len(events_df))
    return raw


if __name__ == "__main__":
    generate_climate_data()
