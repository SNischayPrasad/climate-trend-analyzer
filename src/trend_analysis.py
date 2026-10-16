"""
trend_analysis.py
-----------------
Is the climate really changing, by how much, and is it statistically
significant? Three complementary methods are used - the same trio found in
IPCC / IMD climate reports:

1. Ordinary Least Squares (OLS) linear regression
      slope = average change per year; p-value tests slope != 0.
      Simple, but sensitive to outliers and assumes normal residuals.
2. Mann-Kendall test (non-parametric)
      Asks only "do later values tend to be larger than earlier ones?".
      Robust to outliers and non-normal data -> standard in hydrology/climate.
3. Sen's slope (Theil-Sen estimator)
      Median of all pairwise slopes -> robust magnitude of the trend.

Outputs: trend_summary.csv, decadal_comparison.csv, seasonal_trends.csv
         and figures 06-13.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import TwoSlopeNorm
from scipy import stats
from statsmodels.tsa.seasonal import STL

from src import config
from src.feature_engineering import SEASON_ORDER
from src.utils import get_logger, save_figure, save_table, set_plot_style

logger = get_logger(__name__)

TREND_VARIABLES = {
    "temp_mean": ("Annual mean temperature", "°C"),
    "temp_max_avg": ("Mean daily max temperature", "°C"),
    "temp_min_avg": ("Mean daily min temperature", "°C"),
    "rainfall_total": ("Annual rainfall", "mm"),
    "rainy_days": ("Rainy days per year", "days"),
    "heavy_rain_days": ("Heavy-rain days per year", "days"),
    "max_1day_rain": ("Wettest day of year", "mm"),
    "hot_days": ("Hot days per year (>p90 Tmax)", "days"),
    "cold_nights": ("Cold nights per year (<p10 Tmin)", "days"),
}


# ---------------------------------------------------------------------------
# Statistical tests
# ---------------------------------------------------------------------------
def mann_kendall(x) -> dict:
    """
    Mann-Kendall trend test with tie correction.
    Returns S statistic, Kendall's tau, Z score, two-sided p-value and verdict.
    """
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n < 4:
        raise ValueError("Mann-Kendall needs at least 4 observations")

    # S = sum of signs of all forward differences
    s = 0
    for i in range(n - 1):
        s += np.sign(x[i + 1:] - x[i]).sum()

    # Variance of S, corrected for tied values
    _, counts = np.unique(x, return_counts=True)
    ties = counts[counts > 1]
    var_s = (n * (n - 1) * (2 * n + 5) - np.sum(ties * (ties - 1) * (2 * ties + 5))) / 18

    if s > 0:
        z = (s - 1) / np.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / np.sqrt(var_s)
    else:
        z = 0.0
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    tau = s / (0.5 * n * (n - 1))

    if p < config.SIGNIFICANCE_LEVEL:
        verdict = "increasing" if z > 0 else "decreasing"
    else:
        verdict = "no significant trend"
    return {"S": int(s), "tau": tau, "z": z, "p_value": p, "trend": verdict}


def analyze_series(years, values) -> dict:
    """Run OLS + Mann-Kendall + Sen's slope on one yearly series."""
    years = np.asarray(years, dtype=float)
    values = np.asarray(values, dtype=float)
    ols = stats.linregress(years, values)
    sen_slope, sen_intercept, _, _ = stats.theilslopes(values, years)
    mk = mann_kendall(values)
    first10, last10 = values[:10].mean(), values[-10:].mean()
    return {
        "ols_slope_per_decade": ols.slope * 10,
        "ols_r2": ols.rvalue ** 2,
        "ols_p_value": ols.pvalue,
        "sen_slope_per_decade": sen_slope * 10,
        "mk_tau": mk["tau"],
        "mk_z": mk["z"],
        "mk_p_value": mk["p_value"],
        "trend": mk["trend"],
        "first_decade_mean": first10,
        "last_decade_mean": last10,
        "change_last_vs_first_decade": last10 - first10,
    }


def build_trend_summary(yearly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for city, g in yearly.groupby("city"):
        g = g.sort_values("year")
        for var, (label, unit) in TREND_VARIABLES.items():
            res = analyze_series(g["year"], g[var])
            rows.append({"city": city, "variable": var, "description": label, "unit": unit, **res})
    out = pd.DataFrame(rows)
    num = out.select_dtypes("number").columns
    out[num] = out[num].round(4)
    return out


def build_decadal_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """Average climate per decade - an easy table for non-technical readers."""
    yearly_rain = df.groupby(["city", "decade", "year"])["rainfall_mm"].sum().reset_index()
    rain = yearly_rain.groupby(["city", "decade"])["rainfall_mm"].mean().rename("avg_annual_rainfall_mm")
    temp = df.groupby(["city", "decade"]).agg(avg_temp=("temp_mean", "mean"),
                                              avg_tmax=("temp_max", "mean"),
                                              hot_days_per_year=("hot_day", "sum"))
    years = df.groupby(["city", "decade"])["year"].nunique()
    temp["hot_days_per_year"] = temp["hot_days_per_year"] / years
    return temp.join(rain).round(2).reset_index()


def build_seasonal_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Warming rate per season - reveals *when* in the year change is fastest."""
    rows = []
    seasonal = df.groupby(["city", "season", "year"])["temp_mean"].mean().reset_index()
    for (city, season), g in seasonal.groupby(["city", "season"]):
        res = analyze_series(g["year"], g["temp_mean"])
        rows.append({"city": city, "season": season,
                     "warming_per_decade": round(res["sen_slope_per_decade"], 3),
                     "mk_p_value": round(res["mk_p_value"], 4), "trend": res["trend"]})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------
def plot_temperature_trend(yearly, summary):
    fig, ax = plt.subplots(figsize=(13, 6))
    for city, g in yearly.groupby("city"):
        c = config.CITY_COLORS[city]
        s = summary[(summary.city == city) & (summary.variable == "temp_mean")].iloc[0]
        ax.plot(g["year"], g["temp_mean"], "o-", color=c, alpha=0.45, ms=3.5)
        fit = np.polyfit(g["year"], g["temp_mean"], 1)
        ax.plot(g["year"], np.polyval(fit, g["year"]), color=c, lw=2.5,
                label=f"{city}: {s.sen_slope_per_decade:+.2f} °C/decade (p={s.mk_p_value:.3f})")
    ax.set(title="Annual mean temperature with linear trend", xlabel="Year", ylabel="Temperature (°C)")
    ax.legend(loc="upper left", ncol=2)
    return save_figure(fig, "06_temperature_trend.png")


def plot_rainfall_trend(yearly, summary):
    cities = list(config.CITY_PROFILES)
    fig, axes = plt.subplots(2, 2, figsize=(14, 8), sharex=True)
    for ax, city in zip(axes.flat, cities):
        g = yearly[yearly.city == city]
        s = summary[(summary.city == city) & (summary.variable == "rainfall_total")].iloc[0]
        mean = g["rainfall_total"].mean()
        colors = np.where(g["rainfall_total"] >= mean, "#4c72b0", "#c44e52")
        ax.bar(g["year"], g["rainfall_total"], color=colors, alpha=0.8)
        ax.plot(g["year"], g["rainfall_total"].rolling(5, center=True).mean(), color="black", lw=2,
                label="5-yr moving avg")
        ax.axhline(mean, ls="--", color="grey", lw=1)
        ax.set(title=f"{city}: {s.sen_slope_per_decade:+.0f} mm/decade ({s.trend})", ylabel="mm/year")
        ax.legend(loc="upper left")
    fig.suptitle("Annual rainfall (blue = above average, red = below average)", fontsize=14, fontweight="bold")
    fig.tight_layout()
    return save_figure(fig, "07_rainfall_trend.png")


def plot_warming_stripes(yearly):
    """Ed Hawkins-style 'warming stripes' - one row per city."""
    cities = list(config.CITY_PROFILES)
    fig, axes = plt.subplots(len(cities), 1, figsize=(13, 1.3 * len(cities) + 0.8), sharex=True)
    for ax, city in zip(axes, cities):
        g = yearly[yearly.city == city].sort_values("year")
        anom = g["temp_anomaly"].values
        lim = max(abs(anom.min()), abs(anom.max()))
        ax.imshow(anom[np.newaxis, :], aspect="auto", cmap="RdBu_r",
                  norm=TwoSlopeNorm(0, -lim, lim),
                  extent=[g.year.min() - 0.5, g.year.max() + 0.5, 0, 1])
        ax.set_yticks([]); ax.set_ylabel(city, rotation=0, ha="right", va="center", fontsize=11)
        ax.grid(False)
    axes[0].set_title(f"Warming stripes: annual temperature anomaly vs "
                      f"{config.BASELINE_START}-{config.BASELINE_END} normal (blue = cooler, red = warmer)")
    axes[-1].set_xlabel("Year")
    return save_figure(fig, "08_warming_stripes.png")


def plot_anomaly_heatmap(monthly):
    cities = list(config.CITY_PROFILES)
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    for ax, city in zip(axes.flat, cities):
        pivot = monthly[monthly.city == city].pivot(index="year", columns="month", values="temp_anomaly")
        sns.heatmap(pivot, cmap="RdBu_r", center=0, ax=ax, cbar_kws={"label": "°C"},
                    xticklabels=["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"],
                    yticklabels=5)
        ax.set(title=f"{city}: monthly temperature anomaly", xlabel="Month", ylabel="Year")
    fig.tight_layout()
    return save_figure(fig, "09_monthly_anomaly_heatmap.png")


def plot_decomposition(monthly, city="Delhi"):
    """STL: split the monthly series into trend + seasonal + residual."""
    s = monthly[monthly.city == city].set_index("date")["temp_mean"].asfreq("MS")
    res = STL(s, period=12, robust=True).fit()
    fig, axes = plt.subplots(4, 1, figsize=(13, 10), sharex=True)
    for ax, (name, comp) in zip(axes, [("Observed", s), ("Trend", res.trend),
                                       ("Seasonal", res.seasonal), ("Residual", res.resid)]):
        ax.plot(comp.index, comp.values, color=config.CITY_COLORS[city] if name == "Trend" else "#444")
        ax.set_ylabel(name)
    axes[0].set_title(f"{city}: STL decomposition of monthly mean temperature")
    return save_figure(fig, "10_stl_decomposition.png")


def plot_decadal_comparison(decadal):
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))
    sns.barplot(data=decadal, x="city", y="avg_temp", hue="decade", palette="YlOrRd", ax=axes[0])
    base = decadal.groupby("city")["avg_temp"].min().min()
    axes[0].set_ylim(base - 1.5, decadal["avg_temp"].max() + 0.6)
    axes[0].set(title="Average temperature by decade", ylabel="°C", xlabel="")
    sns.barplot(data=decadal, x="city", y="hot_days_per_year", hue="decade", palette="YlOrRd", ax=axes[1])
    axes[1].set(title="Hot days per year by decade", ylabel="days/year", xlabel="")
    for ax in axes:
        ax.legend(title="Decade", ncol=4, fontsize=9)
    fig.tight_layout()
    return save_figure(fig, "11_decadal_comparison.png")


def plot_extremes_trend(yearly):
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    for city, g in yearly.groupby("city"):
        c = config.CITY_COLORS[city]
        axes[0].plot(g["year"], g["hot_days"].rolling(5, center=True, min_periods=3).mean(), color=c, lw=2, label=city)
        axes[1].plot(g["year"], g["cold_nights"].rolling(5, center=True, min_periods=3).mean(), color=c, lw=2, label=city)
    axes[0].set(title="Hot days per year (5-yr avg)", ylabel="days", xlabel="Year")
    axes[1].set(title="Cold nights per year (5-yr avg)", ylabel="days", xlabel="Year")
    axes[0].legend(); axes[1].legend()
    fig.tight_layout()
    return save_figure(fig, "12_extreme_days_trend.png")


def plot_seasonal_warming(seasonal_trends):
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.barplot(data=seasonal_trends, x="season", y="warming_per_decade", hue="city",
                order=SEASON_ORDER, palette=config.CITY_COLORS, ax=ax)
    ax.set(title="Warming rate by season (Sen's slope)", ylabel="°C per decade", xlabel="")
    ax.legend(ncol=4)
    return save_figure(fig, "13_seasonal_warming_rate.png")


def run_trend_analysis(df, monthly, yearly):
    set_plot_style()
    summary = build_trend_summary(yearly)
    decadal = build_decadal_comparison(df)
    seasonal = build_seasonal_trends(df)
    save_table(summary, "trend_summary.csv")
    save_table(decadal, "decadal_comparison.csv")
    save_table(seasonal, "seasonal_trends.csv")

    for city in config.CITY_PROFILES:
        s = summary[(summary.city == city) & (summary.variable == "temp_mean")].iloc[0]
        logger.info("  %-10s warming %+.2f °C/decade | MK p=%.4f | %s",
                    city, s.sen_slope_per_decade, s.mk_p_value, s.trend)

    for path in [plot_temperature_trend(yearly, summary), plot_rainfall_trend(yearly, summary),
                 plot_warming_stripes(yearly), plot_anomaly_heatmap(monthly),
                 plot_decomposition(monthly), plot_decadal_comparison(decadal),
                 plot_extremes_trend(yearly), plot_seasonal_warming(seasonal)]:
        logger.info("  saved %s", path.name)
    return summary, decadal, seasonal
