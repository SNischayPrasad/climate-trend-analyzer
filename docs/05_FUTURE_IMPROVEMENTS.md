# 🔭 Future Improvements — Upgrade Roadmap

Each upgrade lists **what**, **why it matters**, **how to build it**, and **difficulty**. Do them one at a time; each is a new commit series and a new LinkedIn post.

| # | Upgrade | Difficulty | New skills shown |
|---|---|---|---|
| 1 | Real-data validation (NASA POWER) | ⭐ | APIs, data validation |
| 2 | Region-wise climate comparison | ⭐⭐ | Grouped stats, ANOVA |
| 3 | City-level forecasting with Prophet / XGBoost | ⭐⭐ | ML forecasting, feature lags |
| 4 | Extreme-event analysis (heatwave definitions, return periods) | ⭐⭐ | Extreme value theory |
| 5 | Climate risk scoring | ⭐⭐ | Composite indices, business framing |
| 6 | Pollution–climate relationship | ⭐⭐ | Data joins, correlation vs causation |
| 7 | Automated climate reporting | ⭐⭐ | Scheduling, PDF/HTML reports |
| 8 | Geospatial dashboard | ⭐⭐⭐ | GeoPandas, Folium, maps |
| 9 | Live weather API integration | ⭐⭐⭐ | REST APIs, caching, scheduling |
| 10 | Weather anomaly prediction (ML classifier) | ⭐⭐⭐ | Classification, imbalance handling |
| 11 | Satellite data integration | ⭐⭐⭐⭐ | xarray, NetCDF, remote sensing |

---

### 1. Real-data validation — *do this first*
- **Why:** Shows the pipeline works on observations, not just a simulation.
- **How:** `python -m src.fetch_nasa_power` → `python main.py --source external --input data/external/nasa_power_india.csv`. Compare warming rates with published IMD figures (~0.6–0.7 °C per century for all-India mean; faster in recent decades). Add a section "Simulated vs Real" to the README.

### 2. Region-wise climate comparison
- **Why:** Policy is regional (north vs coastal vs plateau).
- **How:** Add a `region` column in `config.CITY_PROFILES`; add 8–10 cities; compare warming rates with a box plot and a one-way **ANOVA / Kruskal-Wallis** test (`scipy.stats.kruskal`).

### 3. Better city-level forecasting
- **How:** Add `prophet` (`from prophet import Prophet`) or a gradient-boosted model with lag features (`temp_lag_1`, `temp_lag_12`, rolling means) using `XGBRegressor`/`HistGradientBoostingRegressor`. Use **rolling-origin cross-validation** (`sklearn.model_selection.TimeSeriesSplit`). Add the model to the `MODELS` dict in `src/forecasting.py` — the back-test and charts pick it up automatically.

### 4. Extreme-event analysis
- **How:** Implement the IMD heatwave definition (Tmax ≥ 40 °C and departure ≥ 4.5 °C). Fit a **GEV distribution** to annual max rainfall (`scipy.stats.genextreme`) to estimate **return periods** ("a 1-in-50-year rainfall day is X mm"). This is exactly what drainage engineers need.

### 5. Climate risk scoring
- **How:** Build a 0–100 score per city per year from normalised components: warming rate, hot-day frequency, extreme-rain frequency, rainfall variability (coefficient of variation). Weight them (e.g. 30/30/25/15), rank cities, show a leaderboard. Explain weights in the README — business interviewers love this.

### 6. Pollution and climate relationship
- **How:** Download CPCB / OpenAQ PM2.5 data (Kaggle "Air Quality Data in India"). Join on city + date. Analyse PM2.5 vs temperature inversion (low diurnal range), humidity, rainfall washout. Use lagged correlations and be explicit that correlation ≠ causation.

### 7. Automated climate reporting
- **How:** Convert `reports/climate_insights_report.md` to HTML/PDF (`markdown` + `weasyprint`, or `jinja2` templates). Schedule `python main.py` monthly with **GitHub Actions** (`.github/workflows/report.yml` with a `schedule: cron`) and commit the new report automatically.

### 8. Geospatial dashboard
- **How:** Add `lat/lon` per city (already in `fetch_nasa_power.py`). Use `plotly.express.scatter_mapbox` or `folium` to colour cities by warming rate; for gridded data use `geopandas` + India state shapefile for a choropleth.

### 9. Live weather API integration
- **How:** Use **Open-Meteo** (free, no key) — `https://api.open-meteo.com/v1/forecast` for current data and its historical archive API. Fetch daily, append to the dataset, cache results, and show "today vs normal" in the dashboard.

### 10. Weather anomaly prediction
- **How:** Turn anomaly detection into a supervised problem: label = "heatwave starts within 3 days". Features = lags, rolling means, humidity, month. Train `RandomForestClassifier` with `class_weight="balanced"`; evaluate with precision-recall AUC (not accuracy — the classes are imbalanced).

### 11. Satellite data integration
- **How:** Use ERA5 reanalysis (Copernicus CDS) or MODIS land-surface temperature (Google Earth Engine). Read NetCDF with `xarray`, extract city pixels, compare with station-style data. Great for Research Analyst roles.

---

### Engineering upgrades (show software maturity)
- **CI:** GitHub Actions running `pytest` on every push (add the green badge to README).
- **Config file:** move `config.py` constants into `config.yaml`.
- **Docker:** `Dockerfile` so anyone can run `docker run climate-analyzer`.
- **Data versioning:** DVC for datasets.
- **Type hints + linting:** `ruff`, `mypy`, `pre-commit`.
