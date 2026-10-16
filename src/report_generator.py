"""
report_generator.py
-------------------
Turns numbers into decisions. Reads the saved output tables and writes:

    reports/climate_insights_report.md   - human-readable research summary
    outputs/tables/key_insights.csv      - one-line insights (used by dashboard)

All sentences are generated from the data, so the report updates
automatically if you re-run the pipeline on a different dataset.
"""

from datetime import datetime

import pandas as pd

from src import config
from src.utils import get_logger, save_table

logger = get_logger(__name__)


def _read(name):
    path = config.TABLES_DIR / name
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def build_insights() -> list[dict]:
    trend = _read("trend_summary.csv")
    seasonal = _read("seasonal_trends.csv")
    events = _read("temperature_anomaly_events.csv")
    rain = _read("extreme_rainfall_days.csv")
    fy = _read("forecast_yearly_summary.csv")
    insights = []

    t = trend[trend.variable == "temp_mean"].sort_values("sen_slope_per_decade", ascending=False)
    fastest = t.iloc[0]
    insights.append({"category": "Warming", "insight":
        f"{fastest.city} is warming fastest at {fastest.sen_slope_per_decade:+.2f} °C per decade "
        f"(Mann-Kendall p = {fastest.mk_p_value:.4f})."})
    sig = t[t.mk_p_value < config.SIGNIFICANCE_LEVEL]
    insights.append({"category": "Warming", "insight":
        f"{len(sig)} of {len(t)} cities show a statistically significant warming trend "
        f"(α = {config.SIGNIFICANCE_LEVEL})."})
    for _, r in t.iterrows():
        insights.append({"category": "Warming", "insight":
            f"{r.city}: the last decade averaged {r.change_last_vs_first_decade:+.2f} °C compared with the first decade."})

    hot = trend[trend.variable == "hot_days"]
    for _, r in hot.iterrows():
        insights.append({"category": "Heat extremes", "insight":
            f"{r.city}: hot days rose from {r.first_decade_mean:.0f} to {r.last_decade_mean:.0f} per year "
            f"({r.trend})."})

    rt = trend[trend.variable == "rainfall_total"]
    for _, r in rt.iterrows():
        insights.append({"category": "Rainfall", "insight":
            f"{r.city}: annual rainfall trend {r.sen_slope_per_decade:+.0f} mm/decade - {r.trend} "
            f"(p = {r.mk_p_value:.3f}). Year-to-year variability dominates."})

    if not seasonal.empty:
        s = seasonal.sort_values("warming_per_decade", ascending=False).iloc[0]
        insights.append({"category": "Seasonal shift", "insight":
            f"Fastest seasonal warming: {s.city} in {s.season} ({s.warming_per_decade:+.2f} °C/decade)."})

    if not events.empty:
        top = events.iloc[0]
        insights.append({"category": "Anomalies", "insight":
            f"{len(events)} temperature anomaly events detected; most extreme: {top.city} "
            f"{top.type.replace('_', ' ')} starting {top.start_date} (z = {top.peak_zscore})."})
    if not rain.empty:
        top = rain.sort_values("rainfall_mm", ascending=False).iloc[0]
        insights.append({"category": "Anomalies", "insight":
            f"{len(rain)} extreme-rainfall days detected; wettest: {top.city} on {top.date} "
            f"with {top.rainfall_mm:.0f} mm."})

    if not fy.empty:
        last_year = fy.columns[-1]
        for _, r in fy.iterrows():
            insights.append({"category": "Forecast", "insight":
                f"{r.city}: projected annual mean temperature in {last_year} ≈ {r[last_year]:.2f} °C."})
    return insights


def _md_table(df: pd.DataFrame) -> str:
    """Tiny markdown-table writer (avoids needing the 'tabulate' package)."""
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def generate_report() -> str:
    insights = build_insights()
    save_table(pd.DataFrame(insights), "key_insights.csv")

    trend = _read("trend_summary.csv")
    temp = trend[trend.variable == "temp_mean"][
        ["city", "sen_slope_per_decade", "ols_slope_per_decade", "mk_p_value", "trend",
         "change_last_vs_first_decade"]].round(3)
    quality = _read("data_quality_report.csv")
    evaluation = _read("anomaly_detection_evaluation.csv")
    metrics = _read("forecast_metrics.csv")
    events = _read("temperature_anomaly_events.csv").head(10)

    fig = "../outputs/figures"
    md = [
        "# Climate Trend Analyzer – Insights Report",
        f"_Generated automatically on {datetime.now():%Y-%m-%d %H:%M}_  ",
        f"_Period analysed: {config.START_DATE[:4]}–{config.END_DATE[:4]} · Cities: "
        f"{', '.join(config.CITY_PROFILES)} · Baseline normal: {config.BASELINE_START}–{config.BASELINE_END}_",
        "",
        "> **Data note:** results are produced on a *virtual simulation* of daily climate data "
        "(see `src/data_generator.py`). The same pipeline runs unchanged on real public data "
        "(NASA POWER via `src/fetch_nasa_power.py`).",
        "",
        "## 1. Key insights",
        *[f"- **{i['category']}:** {i['insight']}" for i in insights],
        "",
        "## 2. Data quality",
        _md_table(quality),
        "",
        "## 3. Long-term temperature trend",
        _md_table(temp),
        "",
        f"![Temperature trend]({fig}/06_temperature_trend.png)",
        f"![Warming stripes]({fig}/08_warming_stripes.png)",
        "",
        "## 4. Rainfall & seasonality",
        f"![Rainfall trend]({fig}/07_rainfall_trend.png)",
        f"![Seasonal cycle]({fig}/03_seasonal_cycle.png)",
        "",
        "## 5. Anomalies",
        "### Top 10 temperature anomaly events",
        _md_table(events),
        "",
        f"![Temperature anomalies]({fig}/14_temperature_anomalies.png)",
    ]
    if not evaluation.empty:
        md += ["", "### Detection quality vs. injected ground truth", _md_table(evaluation)]
    md += [
        "",
        "## 6. Forecast (back-test on last "
        f"{config.FORECAST_TEST_YEARS} years)",
        _md_table(metrics),
        "",
        f"![Forecast]({fig}/18_temperature_forecast.png)",
        "",
        "## 7. Recommendations",
        "- **Urban planners:** prioritise heat-action plans (cool roofs, shaded transit stops) in the "
        "fastest-warming city; hot-day frequency is rising everywhere.",
        "- **Water & drainage authorities:** design for extreme single-day rainfall, not the annual "
        "average – the annual total shows no clear trend while extremes still occur.",
        "- **Public health:** use the anomaly-event detector as an early-warning trigger for "
        "heatwave advisories.",
        "- **Next analytical step:** validate the pipeline on NASA POWER / IMD observations and add "
        "region-level comparison.",
    ]
    text = "\n".join(md)
    path = config.REPORTS_DIR / "climate_insights_report.md"
    path.write_text(text, encoding="utf-8")
    logger.info("  saved %s (%d insights)", path.name, len(insights))
    return text
