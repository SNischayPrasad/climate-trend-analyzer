"""
anomaly_detection.py
--------------------
Finds unusual climate behaviour with three methods of increasing complexity:

1. Z-score on de-seasonalised, de-trended temperature (daily)
      z = (observed - normal - trend) / typical variability for that month
      |z| > 3  ->  heatwave-like (z > 0) or cold-spell-like (z < 0) day.
      Consecutive anomalous days are merged into one "event".
2. Percentile threshold for extreme rainfall (daily)
      Wet-day rainfall above the city's 99.5th percentile = extreme rain.
3. Isolation Forest (machine learning, monthly)
      Multivariate: flags months whose combination of temperature anomaly,
      rainfall departure and humidity is unusual, even if no single value
      is extreme on its own.

Because the data is SIMULATED we know where extreme events were injected,
so we can EVALUATE detection quality (recall/precision) - something that
is impossible with most real datasets.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from src import config
from src.utils import get_logger, save_figure, save_table, set_plot_style

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# 1. Temperature anomalies (z-score)
# ---------------------------------------------------------------------------
def detect_temperature_anomalies(df: pd.DataFrame, threshold: float = config.ZSCORE_THRESHOLD) -> pd.DataFrame:
    """Flag days whose temperature z-score exceeds the threshold."""
    df = df.copy()
    df["temp_anomaly_flag"] = (df["temp_zscore"].abs() > threshold).astype(int)
    df["anomaly_type"] = np.select(
        [df["temp_zscore"] > threshold, df["temp_zscore"] < -threshold],
        ["hot_anomaly", "cold_anomaly"], default="normal")
    return df


def group_into_events(df: pd.DataFrame) -> pd.DataFrame:
    """Merge consecutive anomalous days (same city & type) into events."""
    flagged = df[df["temp_anomaly_flag"] == 1].sort_values(["city", "date"]).copy()
    if flagged.empty:
        return pd.DataFrame()
    new_event = ((flagged["date"].diff().dt.days != 1)
                 | (flagged["city"] != flagged["city"].shift())
                 | (flagged["anomaly_type"] != flagged["anomaly_type"].shift()))
    flagged["event_id"] = new_event.cumsum()
    events = (flagged.groupby("event_id")
              .agg(city=("city", "first"), type=("anomaly_type", "first"),
                   start_date=("date", "min"), end_date=("date", "max"),
                   duration_days=("date", "count"),
                   peak_temp=("temp_mean", lambda s: s.max() if s.mean() > 0 else s.min()),
                   peak_zscore=("temp_zscore", lambda s: s.loc[s.abs().idxmax()]),
                   mean_anomaly_c=("temp_residual", "mean"))
              .reset_index(drop=True))
    events["severity"] = pd.cut(events["peak_zscore"].abs(), [0, 3.5, 4.5, np.inf],
                                labels=["Moderate", "Severe", "Extreme"])
    num = events.select_dtypes("number").columns
    events[num] = events[num].round(2)
    return events


# ---------------------------------------------------------------------------
# 2. Extreme rainfall (percentile)
# ---------------------------------------------------------------------------
def detect_extreme_rainfall(df: pd.DataFrame, pct: float = config.RAIN_EXTREME_PERCENTILE) -> pd.DataFrame:
    rows = []
    for city, g in df.groupby("city"):
        wet = g.loc[g["rainfall_mm"] > 0, "rainfall_mm"]
        thr = np.percentile(wet, pct)
        ext = g[g["rainfall_mm"] > thr][["city", "date", "rainfall_mm", "season"]].copy()
        ext["threshold_mm"] = round(thr, 1)
        rows.append(ext)
    return pd.concat(rows).sort_values(["city", "date"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# 3. Isolation Forest on monthly features
# ---------------------------------------------------------------------------
def detect_monthly_anomalies_iforest(monthly: pd.DataFrame) -> pd.DataFrame:
    monthly = monthly.copy()
    # Rainfall departure from the normal for that calendar month (in std units)
    grp = monthly.groupby(["city", "month"])["rainfall_mm"]
    monthly["rain_departure"] = (monthly["rainfall_mm"] - grp.transform("mean")) / grp.transform("std").replace(0, 1)
    hum = monthly.groupby(["city", "month"])["humidity_pct"]
    monthly["humidity_departure"] = monthly["humidity_pct"] - hum.transform("mean")
    features = ["temp_anomaly", "rain_departure", "humidity_departure"]

    out = []
    for city, g in monthly.groupby("city"):
        g = g.copy()
        X = StandardScaler().fit_transform(g[features].fillna(0))
        model = IsolationForest(n_estimators=300, contamination=config.ISOLATION_CONTAMINATION,
                                random_state=config.RANDOM_SEED)
        g["iforest_flag"] = (model.fit_predict(X) == -1).astype(int)
        g["iforest_score"] = -model.score_samples(X)          # higher = more unusual
        out.append(g)
    return pd.concat(out, ignore_index=True)


# ---------------------------------------------------------------------------
# Evaluation against simulation ground truth
# ---------------------------------------------------------------------------
def evaluate_against_ground_truth(df: pd.DataFrame, extreme_rain: pd.DataFrame) -> pd.DataFrame:
    if not config.INJECTED_EVENTS_FILE.exists():
        logger.info("  no ground-truth file (real data?) - skipping evaluation")
        return pd.DataFrame()
    truth = pd.read_csv(config.INJECTED_EVENTS_FILE, parse_dates=["start_date", "end_date"])
    rows = []

    # --- temperature events ---
    for etype, flag_type in [("heatwave", "hot_anomaly"), ("cold_spell", "cold_anomaly")]:
        t = truth[truth.event_type == etype]
        flagged = df[df.anomaly_type == flag_type]
        flagged_keys = set(zip(flagged.city, flagged.date))
        # True event days (+-1 day tolerance for gradual onset)
        true_days = set()
        detected = 0
        for _, e in t.iterrows():
            days = pd.date_range(e.start_date - pd.Timedelta(days=1), e.end_date + pd.Timedelta(days=1))
            keys = {(e.city, d) for d in days}
            true_days |= keys
            detected += bool(keys & flagged_keys)
        precision = len(flagged_keys & true_days) / max(len(flagged_keys), 1)
        rows.append({"event_type": etype, "injected_events": len(t), "events_detected": detected,
                     "event_recall": detected / max(len(t), 1), "flagged_days": len(flagged_keys),
                     "day_precision": precision})

    # --- rainfall events ---
    t = truth[truth.event_type == "extreme_rain"]
    flagged_keys = set(zip(extreme_rain.city, extreme_rain.date))
    true_keys = set(zip(t.city, t.start_date))
    detected = len(flagged_keys & true_keys)
    rows.append({"event_type": "extreme_rain", "injected_events": len(t), "events_detected": detected,
                 "event_recall": detected / max(len(t), 1), "flagged_days": len(flagged_keys),
                 "day_precision": detected / max(len(flagged_keys), 1)})
    return pd.DataFrame(rows).round(3)


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------
def plot_temperature_anomalies(df):
    cities = list(config.CITY_PROFILES)
    fig, axes = plt.subplots(len(cities), 1, figsize=(15, 11), sharex=True)
    for ax, city in zip(axes, cities):
        g = df[df.city == city]
        ax.plot(g["date"], g["temp_residual"], color="#999", lw=0.4, alpha=0.7)
        hot = g[g.anomaly_type == "hot_anomaly"]
        cold = g[g.anomaly_type == "cold_anomaly"]
        ax.scatter(hot["date"], hot["temp_residual"], color="#d62728", s=14, label=f"Hot anomaly ({len(hot)} days)", zorder=3)
        ax.scatter(cold["date"], cold["temp_residual"], color="#1f77b4", s=14, label=f"Cold anomaly ({len(cold)} days)", zorder=3)
        ax.set_ylabel(f"{city}\n°C")
        ax.legend(loc="upper left", ncol=2, fontsize=9, frameon=True, framealpha=0.9)
    axes[0].set_title(f"Daily temperature departures from normal (de-trended); |z| > {config.ZSCORE_THRESHOLD} flagged")
    fig.tight_layout()
    return save_figure(fig, "14_temperature_anomalies.png")


def plot_extreme_rainfall(df, extreme_rain):
    cities = list(config.CITY_PROFILES)
    fig, axes = plt.subplots(2, 2, figsize=(15, 8), sharex=True)
    for ax, city in zip(axes.flat, cities):
        g = df[df.city == city]
        e = extreme_rain[extreme_rain.city == city]
        ax.plot(g["date"], g["rainfall_mm"], color="#4c72b0", lw=0.4)
        ax.scatter(e["date"], e["rainfall_mm"], color="#d62728", s=18, zorder=3, label=f"{len(e)} extreme days")
        if len(e):
            ax.axhline(e["threshold_mm"].iloc[0], ls="--", color="#d62728", lw=1,
                       label=f"p{config.RAIN_EXTREME_PERCENTILE} = {e['threshold_mm'].iloc[0]} mm")
        ax.set(title=city, ylabel="mm/day")
        ax.legend(loc="upper left", fontsize=9)
    fig.suptitle("Extreme daily rainfall detection", fontsize=14, fontweight="bold")
    fig.tight_layout()
    return save_figure(fig, "15_extreme_rainfall.png")


def plot_iforest(monthly_flags):
    fig, ax = plt.subplots(figsize=(11, 7))
    normal = monthly_flags[monthly_flags.iforest_flag == 0]
    anom = monthly_flags[monthly_flags.iforest_flag == 1]
    ax.scatter(normal["temp_anomaly"], normal["rain_departure"], s=10, alpha=0.3, color="#888", label="Normal month")
    for city, g in anom.groupby("city"):
        ax.scatter(g["temp_anomaly"], g["rain_departure"], s=60, edgecolor="black",
                   color=config.CITY_COLORS[city], label=f"Anomalous month – {city}")
    ax.axhline(0, color="black", lw=0.6); ax.axvline(0, color="black", lw=0.6)
    ax.set(title="Isolation Forest: unusual months (temperature × rainfall × humidity)",
           xlabel="Monthly temperature anomaly (°C)", ylabel="Rainfall departure (std units)")
    ax.legend(fontsize=9)
    return save_figure(fig, "16_isolation_forest_months.png")


def run_anomaly_detection(df, monthly):
    set_plot_style()
    df = detect_temperature_anomalies(df)
    events = group_into_events(df)
    extreme_rain = detect_extreme_rainfall(df)
    monthly_flags = detect_monthly_anomalies_iforest(monthly)
    evaluation = evaluate_against_ground_truth(df, extreme_rain)

    save_table(events.sort_values("peak_zscore", key=abs, ascending=False), "temperature_anomaly_events.csv")
    save_table(extreme_rain, "extreme_rainfall_days.csv")
    flagged_months = monthly_flags.loc[monthly_flags.iforest_flag == 1,
                                       ["city", "date", "temp_mean", "temp_anomaly", "rainfall_mm",
                                        "rain_departure", "humidity_pct", "iforest_score"]]
    flagged_months["date"] = flagged_months["date"].dt.strftime("%Y-%m")
    save_table(flagged_months.round(3).sort_values("iforest_score", ascending=False),
               "anomalous_months_iforest.csv")
    if not evaluation.empty:
        save_table(evaluation, "anomaly_detection_evaluation.csv")
        for _, r in evaluation.iterrows():
            logger.info("  %-13s recall %.0f%% (%d/%d events) | day precision %.0f%%",
                        r.event_type, r.event_recall * 100, r.events_detected,
                        r.injected_events, r.day_precision * 100)

    logger.info("  %d temperature anomaly events, %d extreme-rain days, %d anomalous months",
                len(events), len(extreme_rain), int(monthly_flags.iforest_flag.sum()))
    for path in [plot_temperature_anomalies(df), plot_extreme_rainfall(df, extreme_rain), plot_iforest(monthly_flags)]:
        logger.info("  saved %s", path.name)
    return df, events, extreme_rain, monthly_flags, evaluation
