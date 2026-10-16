"""
streamlit_app.py - interactive Climate Trend Analyzer dashboard
================================================================
Run AFTER the pipeline (python main.py):

    streamlit run app/streamlit_app.py

Reads the processed data + output tables, so it opens instantly and does
not re-run any heavy computation.
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))
from src import config  # noqa: E402

st.set_page_config(page_title="Climate Trend Analyzer", page_icon="🌡️", layout="wide")


@st.cache_data
def load():
    if not config.FEATURES_FILE.exists():
        return None
    t = config.TABLES_DIR
    return {
        "daily": pd.read_csv(config.FEATURES_FILE, parse_dates=["date"]),
        "monthly": pd.read_csv(config.MONTHLY_FILE, parse_dates=["date"]),
        "yearly": pd.read_csv(config.YEARLY_FILE),
        "trend": pd.read_csv(t / "trend_summary.csv"),
        "events": pd.read_csv(t / "temperature_anomaly_events.csv"),
        "rain": pd.read_csv(t / "extreme_rainfall_days.csv"),
        "forecast": pd.read_csv(t / "temperature_forecast.csv", parse_dates=["date"]),
        "metrics": pd.read_csv(t / "forecast_metrics.csv"),
        "insights": pd.read_csv(t / "key_insights.csv"),
        "quality": pd.read_csv(t / "data_quality_report.csv"),
    }


data = load()
if data is None:
    st.error("No processed data found. Run `python main.py` first, then reload this page.")
    st.stop()

# ---------------- Sidebar ----------------
st.sidebar.title("🌡️ Climate Trend Analyzer")
cities = list(config.CITY_PROFILES)
city = st.sidebar.selectbox("City", cities)
yr_min, yr_max = int(data["yearly"].year.min()), int(data["yearly"].year.max())
years = st.sidebar.slider("Year range", yr_min, yr_max, (yr_min, yr_max))
st.sidebar.caption("Data: virtual simulation of daily climate (1990–2024). "
                   "Swap in NASA POWER data with `src/fetch_nasa_power.py`.")

daily = data["daily"][(data["daily"].city == city) & data["daily"].year.between(*years)]
yearly = data["yearly"][(data["yearly"].city == city) & data["yearly"].year.between(*years)]
trend = data["trend"][data["trend"].city == city].set_index("variable")

# ---------------- Header + KPIs ----------------
st.title(f"Climate Trend Analyzer — {city}")
k1, k2, k3, k4 = st.columns(4)
t = trend.loc["temp_mean"]
k1.metric("Warming rate (per decade)", f"{t.sen_slope_per_decade:+.2f} °C", t.trend)
k2.metric("Last vs first decade", f"{t.change_last_vs_first_decade:+.2f} °C")
h = trend.loc["hot_days"]
k3.metric("Hot days / year (latest decade)", f"{h.last_decade_mean:.0f}",
          f"{h.last_decade_mean - h.first_decade_mean:+.0f} vs 1990s")
r = trend.loc["rainfall_total"]
k4.metric("Avg annual rainfall", f"{yearly.rainfall_total.mean():.0f} mm",
          f"{r.sen_slope_per_decade:+.0f} mm/decade", delta_color="off")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Trends", "🗓️ Seasonality", "⚠️ Anomalies",
                                         "🔮 Forecast", "💡 Insights"])

with tab1:
    fig = px.scatter(yearly, x="year", y="temp_mean", trendline="ols",
                     title="Annual mean temperature with OLS trend", labels={"temp_mean": "°C"})
    fig.update_traces(marker=dict(color=config.CITY_COLORS[city], size=8))
    st.plotly_chart(fig, width="stretch")
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.bar(yearly, x="year", y="rainfall_total", title="Annual rainfall (mm)"),
                    width="stretch")
    c2.plotly_chart(px.line(yearly, x="year", y=["hot_days", "cold_nights"],
                            title="Hot days vs cold nights per year",
                            color_discrete_map={"hot_days": "#d62728", "cold_nights": "#1f77b4"},
                            labels={"value": "days per year", "variable": ""}), width="stretch")
    st.subheader("Statistical trend tests")
    st.dataframe(trend[["description", "unit", "sen_slope_per_decade", "ols_slope_per_decade",
                        "mk_p_value", "trend"]].round(3), width="stretch")

with tab2:
    pivot = (data["monthly"][(data["monthly"].city == city)]
             .pivot(index="year", columns="month", values="temp_anomaly"))
    fig = px.imshow(pivot, color_continuous_scale="RdBu_r", color_continuous_midpoint=0, aspect="auto",
                    title="Monthly temperature anomaly (°C) vs 1991–2020 normal")
    st.plotly_chart(fig, width="stretch")
    clim = daily.groupby("month").agg(temp=("temp_mean", "mean"),
                                      rain=("rainfall_mm", "sum")).reset_index()
    clim["rain"] /= daily.year.nunique()
    fig = go.Figure()
    fig.add_bar(x=clim.month, y=clim.rain, name="Rainfall (mm/month)", yaxis="y2", opacity=0.4)
    fig.add_scatter(x=clim.month, y=clim.temp, name="Mean temp (°C)", mode="lines+markers",
                    line=dict(color=config.CITY_COLORS[city], width=3))
    fig.update_layout(title="Average yearly cycle", yaxis=dict(title="°C"),
                      yaxis2=dict(title="mm", overlaying="y", side="right"))
    st.plotly_chart(fig, width="stretch")

with tab3:
    ev = data["events"][data["events"].city == city]
    fig = px.line(daily, x="date", y="temp_residual", title="Daily temperature departure (de-trended)")
    fig.update_traces(line=dict(color="lightgrey", width=1))
    flagged = daily[daily.temp_zscore.abs() > config.ZSCORE_THRESHOLD]
    fig.add_scatter(x=flagged.date, y=flagged.temp_residual, mode="markers", name="Anomaly",
                    marker=dict(color=flagged.temp_zscore.gt(0).map({True: "red", False: "blue"}), size=6))
    st.plotly_chart(fig, width="stretch")
    c1, c2 = st.columns(2)
    c1.subheader(f"Temperature anomaly events ({len(ev)})")
    c1.dataframe(ev, width="stretch", hide_index=True)
    rn = data["rain"][data["rain"].city == city]
    c2.subheader(f"Extreme rainfall days ({len(rn)})")
    c2.dataframe(rn, width="stretch", hide_index=True)

with tab4:
    fc = data["forecast"][data["forecast"].city == city]
    hist = data["monthly"][(data["monthly"].city == city) & (data["monthly"].date >= "2015-01-01")]
    fig = go.Figure()
    fig.add_scatter(x=hist.date, y=hist.temp_mean, name="Observed", line=dict(color="black"))
    if fc["lower"].notna().all():
        fig.add_scatter(x=pd.concat([fc.date, fc.date[::-1]]), y=pd.concat([fc.upper, fc.lower[::-1]]),
                        fill="toself", fillcolor="rgba(214,39,40,0.15)", line=dict(width=0),
                        name="95% interval")
    fig.add_scatter(x=fc.date, y=fc.forecast, name=f"Forecast ({fc.model.iloc[0]})",
                    line=dict(color=config.CITY_COLORS[city], width=3))
    fig.update_layout(title="5-year monthly temperature forecast", yaxis_title="°C")
    st.plotly_chart(fig, width="stretch")
    st.subheader("Back-test accuracy (last 3 years held out)")
    st.dataframe(data["metrics"][data["metrics"].city == city], width="stretch", hide_index=True)

with tab5:
    for cat, g in data["insights"].groupby("category", sort=False):
        st.markdown(f"#### {cat}")
        for txt in g.insight:
            st.markdown(f"- {txt}")
    st.subheader("Data quality report")
    st.dataframe(data["quality"], width="stretch", hide_index=True)
