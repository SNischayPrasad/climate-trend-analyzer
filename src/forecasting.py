"""
forecasting.py
--------------
Estimates future monthly temperature for each city.

Three models are compared on a hold-out period (the last 3 years), exactly as
you would in industry - never trust a forecast you have not back-tested:

1. Seasonal Naive   : "next January = last January". The baseline to beat.
2. Linear Regression: temp = trend * time + month effects (scikit-learn).
                      Transparent and easy to explain.
3. SARIMA           : Seasonal ARIMA (statsmodels). Models autocorrelation,
                      seasonality and drift; gives confidence intervals.

The model with the lowest RMSE for each city is refitted on ALL data and
used to forecast the next 5 years.
"""

import pickle
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.statespace.sarimax import SARIMAX

from src import config
from src.utils import get_logger, save_figure, save_table, set_plot_style

logger = get_logger(__name__)
warnings.filterwarnings("ignore")          # statsmodels convergence chatter

SARIMA_ORDER = (1, 0, 1)
SARIMA_SEASONAL_ORDER = (0, 1, 1, 12)


# ---------------------------------------------------------------------------
# Models - each takes a train Series (monthly, DatetimeIndex) and a horizon
# ---------------------------------------------------------------------------
def seasonal_naive(train: pd.Series, horizon: int) -> pd.DataFrame:
    last_year = train.iloc[-12:].values
    values = np.tile(last_year, horizon // 12 + 1)[:horizon]
    idx = pd.date_range(train.index[-1] + pd.offsets.MonthBegin(), periods=horizon, freq="MS")
    return pd.DataFrame({"forecast": values}, index=idx)


def _design_matrix(index: pd.DatetimeIndex, origin: pd.Timestamp) -> pd.DataFrame:
    t = (index.year - origin.year) * 12 + (index.month - origin.month)
    X = pd.get_dummies(pd.Categorical(index.month, categories=range(1, 13)), prefix="m", drop_first=True)
    X.insert(0, "t", t)
    return X.astype(float)


def linear_trend_seasonal(train: pd.Series, horizon: int) -> pd.DataFrame:
    origin = train.index[0]
    model = LinearRegression().fit(_design_matrix(train.index, origin), train.values)
    idx = pd.date_range(train.index[-1] + pd.offsets.MonthBegin(), periods=horizon, freq="MS")
    pred = model.predict(_design_matrix(idx, origin))
    resid_std = np.std(train.values - model.predict(_design_matrix(train.index, origin)))
    return pd.DataFrame({"forecast": pred, "lower": pred - 1.96 * resid_std,
                         "upper": pred + 1.96 * resid_std}, index=idx)


def fit_sarima(train: pd.Series):
    return SARIMAX(train, order=SARIMA_ORDER, seasonal_order=SARIMA_SEASONAL_ORDER,
                   trend="c", enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)


def sarima(train: pd.Series, horizon: int, return_model: bool = False):
    res = fit_sarima(train)
    fc = res.get_forecast(steps=horizon)
    ci = fc.conf_int(alpha=0.05)
    out = pd.DataFrame({"forecast": fc.predicted_mean.values, "lower": ci.iloc[:, 0].values,
                        "upper": ci.iloc[:, 1].values}, index=fc.predicted_mean.index)
    return (out, res) if return_model else out


MODELS = {"Seasonal Naive": seasonal_naive,
          "Linear Trend + Seasonality": linear_trend_seasonal,
          "SARIMA": sarima}


def _metrics(actual, predicted) -> dict:
    return {"MAE": mean_absolute_error(actual, predicted),
            "RMSE": np.sqrt(mean_squared_error(actual, predicted)),
            "MAPE_%": np.mean(np.abs((actual - predicted) / actual)) * 100}


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
def run_forecasting(monthly: pd.DataFrame):
    set_plot_style()
    test_len = config.FORECAST_TEST_YEARS * 12
    metrics_rows, backtests, forecasts = [], {}, []

    for city, g in monthly.groupby("city"):
        series = g.set_index("date")["temp_mean"].asfreq("MS").interpolate()
        train, test = series.iloc[:-test_len], series.iloc[-test_len:]

        # ---- Back-test every model on the hold-out period ----
        backtests[city] = {"train": train, "test": test}
        for name, fn in MODELS.items():
            pred = fn(train, test_len)
            backtests[city][name] = pred
            m = _metrics(test.values, pred["forecast"].values)
            metrics_rows.append({"city": city, "model": name, **m})

        # ---- Pick best model, refit on all data, forecast ahead ----
        city_metrics = [r for r in metrics_rows if r["city"] == city]
        best = min(city_metrics, key=lambda r: r["RMSE"])["model"]
        if best == "SARIMA":
            fc, res = sarima(series, config.FORECAST_HORIZON_MONTHS, return_model=True)
            res.remove_data()                      # keep the saved file small
            with open(config.MODELS_DIR / f"sarima_{city.lower()}.pkl", "wb") as f:
                pickle.dump(res, f)
        else:
            fc = MODELS[best](series, config.FORECAST_HORIZON_MONTHS)
        fc = fc.reset_index().rename(columns={"index": "date"})
        fc["city"], fc["model"] = city, best
        forecasts.append(fc)
        logger.info("  %-10s best model: %-27s (RMSE %.3f °C)", city, best,
                    min(r["RMSE"] for r in city_metrics))

    metrics = pd.DataFrame(metrics_rows).round(3)
    forecast_df = pd.concat(forecasts, ignore_index=True).round(2)
    save_table(metrics, "forecast_metrics.csv")
    save_table(forecast_df, "temperature_forecast.csv")

    # Yearly view of the forecast: easier to communicate
    fy = forecast_df.assign(year=forecast_df["date"].dt.year).groupby(["city", "year"])["forecast"].mean().round(2)
    save_table(fy.unstack("year").reset_index(), "forecast_yearly_summary.csv")

    for path in [plot_backtest(backtests, metrics), plot_forecast(monthly, forecast_df), plot_model_comparison(metrics)]:
        logger.info("  saved %s", path.name)
    return metrics, forecast_df


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------
def plot_backtest(backtests, metrics):
    cities = list(config.CITY_PROFILES)
    fig, axes = plt.subplots(2, 2, figsize=(15, 8))
    styles = {"Seasonal Naive": ("#999", ":"), "Linear Trend + Seasonality": ("#2ca02c", "--"), "SARIMA": ("#d62728", "-")}
    for ax, city in zip(axes.flat, cities):
        b = backtests[city]
        ax.plot(b["train"].index[-48:], b["train"].iloc[-48:], color="black", lw=1, label="Train (last 4 yrs)")
        ax.plot(b["test"].index, b["test"], color="black", lw=2, label="Actual (hold-out)")
        for name, (c, ls) in styles.items():
            rmse = metrics[(metrics.city == city) & (metrics.model == name)]["RMSE"].iloc[0]
            ax.plot(b[name].index, b[name]["forecast"], color=c, ls=ls, lw=1.8, label=f"{name} (RMSE {rmse:.2f})")
        ax.set(title=f"{city}: back-test on last {config.FORECAST_TEST_YEARS} years", ylabel="°C")
        ax.legend(fontsize=8, loc="lower left", frameon=True, framealpha=0.9)
    fig.tight_layout()
    return save_figure(fig, "17_forecast_backtest.png")


def plot_forecast(monthly, forecast_df):
    cities = list(config.CITY_PROFILES)
    fig, axes = plt.subplots(2, 2, figsize=(15, 8))
    for ax, city in zip(axes.flat, cities):
        hist = monthly[(monthly.city == city) & (monthly.date >= "2015-01-01")]
        fc = forecast_df[forecast_df.city == city]
        c = config.CITY_COLORS[city]
        ax.plot(hist["date"], hist["temp_mean"], color="black", lw=1, label="Observed")
        ax.plot(fc["date"], fc["forecast"], color=c, lw=2, label=f"Forecast ({fc['model'].iloc[0]})")
        if "lower" in fc and fc["lower"].notna().all():
            ax.fill_between(fc["date"], fc["lower"], fc["upper"], color=c, alpha=0.2, label="95% interval")
        ax.set(title=f"{city}: monthly temperature forecast to {fc['date'].dt.year.max()}", ylabel="°C")
        ax.legend(fontsize=8, loc="lower left", frameon=True, framealpha=0.9)
    fig.tight_layout()
    return save_figure(fig, "18_temperature_forecast.png")


def plot_model_comparison(metrics):
    import seaborn as sns
    fig, ax = plt.subplots(figsize=(11, 5))
    sns.barplot(data=metrics, x="city", y="RMSE", hue="model", palette=["#999", "#2ca02c", "#d62728"], ax=ax)
    ax.set(title="Forecast error on hold-out period (lower is better)", ylabel="RMSE (°C)", xlabel="")
    ax.legend(ncol=3)
    return save_figure(fig, "19_model_comparison.png")
