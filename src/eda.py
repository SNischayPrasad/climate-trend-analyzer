"""
eda.py
------
Exploratory Data Analysis: understand the data BEFORE modelling it.

Answers questions like:
    - How much data was missing / broken?          -> 01_missing_values.png
    - What do temperature & rainfall look like?    -> 02_distributions.png
    - What is the typical yearly cycle per city?   -> 03_seasonal_cycle.png
    - How do the variables relate to each other?   -> 04_correlation_heatmap.png
    - How different are the seasons?               -> 05_season_boxplot.png
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src import config
from src.feature_engineering import SEASON_ORDER
from src.utils import get_logger, save_figure, save_table, set_plot_style

logger = get_logger(__name__)
MONTH_LABELS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]


def descriptive_statistics(df: pd.DataFrame) -> pd.DataFrame:
    """Mean / std / min / max of key variables per city."""
    stats = (df.groupby("city")[["temp_mean", "temp_max", "temp_min",
                                 "rainfall_mm", "humidity_pct"]]
             .agg(["mean", "std", "min", "max"]).round(2))
    stats.columns = ["_".join(c) for c in stats.columns]
    return stats.reset_index()


def plot_missing_values(path=config.TABLES_DIR / "missing_values_by_column.csv"):
    missing = pd.read_csv(path)
    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = range(len(missing))
    ax.bar([i - 0.2 for i in x], missing["missing"], width=0.4, label="Missing (NaN)", color="#4c72b0")
    ax.bar([i + 0.2 for i in x], missing["sentinel_errors"], width=0.4,
           label="Sensor error codes (-999/999)", color="#dd8452")
    ax.set_xticks(list(x), missing["column"])
    ax.set_ylabel("Number of records")
    ax.set_title("Raw data quality issues by column (before cleaning)")
    ax.legend()
    return save_figure(fig, "01_missing_values.png")


def plot_distributions(df: pd.DataFrame):
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for city, g in df.groupby("city"):
        sns.kdeplot(g["temp_mean"], ax=axes[0], label=city, color=config.CITY_COLORS[city], fill=True, alpha=0.15)
        wet = g.loc[g["rainfall_mm"] > 0, "rainfall_mm"]
        sns.histplot(wet, ax=axes[1], label=city, color=config.CITY_COLORS[city],
                     bins=60, element="step", fill=False, log_scale=(False, True))
    axes[0].set(title="Daily mean temperature distribution", xlabel="Temperature (°C)")
    axes[1].set(title="Rainfall on wet days (log count)", xlabel="Rainfall (mm/day)")
    axes[0].legend(); axes[1].legend()
    return save_figure(fig, "02_distributions.png")


def plot_seasonal_cycle(df: pd.DataFrame):
    """Monthly climatology: temperature line + rainfall bars, one panel per city."""
    cities = list(config.CITY_PROFILES)
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), sharex=True)
    for ax, city in zip(axes.flat, cities):
        g = df[df["city"] == city]
        n_years = g["year"].nunique()
        clim = g.groupby("month").agg(t=("temp_mean", "mean"), tmax=("temp_max", "mean"),
                                      tmin=("temp_min", "mean"), rain=("rainfall_mm", "sum"))
        clim["rain"] /= n_years                                   # mm per month
        ax2 = ax.twinx()
        ax2.bar(clim.index, clim["rain"], color="#4c72b0", alpha=0.35, label="Rainfall")
        ax2.set_ylabel("Rainfall (mm/month)", color="#4c72b0")
        ax2.grid(False)
        ax.fill_between(clim.index, clim["tmin"], clim["tmax"], color=config.CITY_COLORS[city], alpha=0.15)
        ax.plot(clim.index, clim["t"], marker="o", color=config.CITY_COLORS[city], lw=2.5)
        ax.set_zorder(ax2.get_zorder() + 1); ax.patch.set_visible(False)
        ax.set(title=f"{city}: average yearly cycle", ylabel="Temperature (°C)")
        ax.set_xticks(range(1, 13), MONTH_LABELS)
    fig.suptitle("Seasonal climate patterns (line = mean temp, band = min–max, bars = rainfall)",
                 fontsize=14, fontweight="bold")
    fig.tight_layout()
    return save_figure(fig, "03_seasonal_cycle.png")


def plot_correlation(df: pd.DataFrame):
    cols = ["temp_mean", "temp_max", "temp_min", "diurnal_range", "rainfall_mm", "humidity_pct"]
    corr = df[cols].corr()
    fig, ax = plt.subplots(figsize=(8, 6.5))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", vmin=-1, vmax=1, ax=ax, square=True)
    ax.set_title("Correlation between climate variables (all cities, daily)")
    return save_figure(fig, "04_correlation_heatmap.png")


def plot_season_boxplot(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(13, 5.5))
    sns.boxplot(data=df, x="season", y="temp_mean", hue="city", order=SEASON_ORDER,
                palette=config.CITY_COLORS, fliersize=1, ax=ax)
    ax.set(title="Temperature by season and city", xlabel="", ylabel="Daily mean temperature (°C)")
    ax.legend(ncol=4, loc="upper right")
    return save_figure(fig, "05_season_boxplot.png")


def run_eda(df: pd.DataFrame) -> pd.DataFrame:
    set_plot_style()
    stats = descriptive_statistics(df)
    save_table(stats, "descriptive_statistics.csv")
    save_table(df.head(20), "dataset_preview.csv")
    for fn, arg in [(plot_missing_values, None), (plot_distributions, df),
                    (plot_seasonal_cycle, df), (plot_correlation, df), (plot_season_boxplot, df)]:
        path = fn() if arg is None else fn(arg)
        logger.info("  saved %s", path.name)
    return stats
