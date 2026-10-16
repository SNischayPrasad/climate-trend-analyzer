# 📘 Climate Trend Analyzer — Complete Project Guide

Covers deliverable sections **A–I**: explanation, tech-stack options, chosen approach, architecture, implementation phases, folder structure, installation, file-by-file code guide, virtual simulation workflow and how to run.

---

## A. Project explanation

### A1. In simple language
Imagine you write down the temperature and rainfall in your city every day for 35 years. Any single day tells you little — one hot day is just weather. But when you look at all 12,000+ days together you can ask:
- *Are summers getting hotter than they used to be?*
- *Is the monsoon getting weaker, stronger or more erratic?*
- *Which days were truly unusual?*
- *What will next year probably look like?*

A **Climate Trend Analyzer** is a program that answers those questions automatically and shows the answers as charts and plain sentences.

### A2. In technical language
A Climate Trend Analyzer is a **time-series analytics pipeline** that ingests multivariate daily meteorological observations, performs **data-quality control**, computes **climatological normals** (e.g. the WMO 1991–2020 reference period), derives **anomalies**, tests for **monotonic trends** using parametric (OLS) and non-parametric (Mann-Kendall, Theil–Sen) methods, applies **seasonal-trend decomposition** (STL), detects **univariate and multivariate anomalies** (z-score, percentile thresholds, Isolation Forest), and produces **back-tested forecasts** (SARIMA, regression) with uncertainty intervals.

### A3. What problem does it solve?
Climate signals are small (tenths of a degree per decade) and hidden under large seasonal cycles and day-to-day weather noise. Raw station data is also messy. The analyzer separates **signal from noise**, quantifies it with **statistical confidence**, and flags **extreme events** — turning data into decisions.

### A4. Why it matters & who uses it
| User | Use case |
|---|---|
| **Governments / IMD** | Annual climate statements; state action plans on climate change; heatwave declarations |
| **Research organisations (IITM, universities, IPCC authors)** | Detecting and attributing regional warming; validating climate models |
| **Climate analysts / ESG consultancies** | Physical climate-risk scoring for companies, banks and insurers |
| **Smart-city planners** | Urban heat-island mitigation, cooling centres, tree-cover planning, drainage design |
| **Environmental agencies** | Monitoring drought, extreme rainfall, links with air pollution |
| **Agriculture & insurance** | Sowing calendars, crop-yield risk, weather-index insurance payouts |

### A5. What climate trend analysis reveals
- **Temperature change** — warming rate in °C/decade and its significance.
- **Rainfall variation** — change in totals, rainy days and intensity (heavy-rain days, wettest day).
- **Seasonal shifts** — which season warms fastest; whether the monsoon peak moves.
- **Climate anomalies** — heatwaves, cold spells, cloudbursts, unusual months.
- **Long-term patterns** — decade-by-decade comparison, warming stripes, decomposition into trend + season + noise.

### A6. Complete workflow
| Stage | What happens | Module |
|---|---|---|
| 1. Data collection | Simulate (or download) daily temp, rainfall, humidity | `data_generator.py`, `fetch_nasa_power.py` |
| 2. Data cleaning | Remove duplicates, error codes, impossible values; fill gaps | `preprocessing.py` |
| 3. EDA | Distributions, seasonal cycles, correlations | `eda.py` |
| 4. Feature engineering | Seasons, climate normals, anomalies, z-scores, hot days, aggregates | `feature_engineering.py` |
| 5. Trend analysis | OLS, Mann-Kendall, Sen's slope, STL, decadal tables | `trend_analysis.py` |
| 6. Anomaly detection | Z-score events, rainfall percentiles, Isolation Forest | `anomaly_detection.py` |
| 7. Forecasting | Naive vs Linear vs SARIMA back-test, 5-year forecast | `forecasting.py` |
| 8. Visualisation & reporting | 19 charts, 15 tables, markdown report | all modules + `report_generator.py` |
| 9. Insights | Auto-generated sentences + dashboard | `report_generator.py`, `app/streamlit_app.py` |

---

## B. Tech-stack options

| | **Option A — Easiest** | **Option B — Intermediate** ✅ | **Option C — Advanced** |
|---|---|---|---|
| **Tools** | Python, pandas, Matplotlib, Jupyter, one CSV | + NumPy, Seaborn, Plotly, SciPy, scikit-learn, statsmodels, Streamlit, pytest | + Prophet / XGBoost / LSTM (TensorFlow), xarray/NetCDF (ERA5), GeoPandas, Docker, GitHub Actions, cloud deploy |
| **Analysis** | Rolling averages, yearly means, simple linear trend line | Climate normals, Mann-Kendall + Sen's slope, STL, Z-score + Isolation Forest, SARIMA vs regression back-test | Deep-learning forecasts, gridded spatial trends, extreme-value theory, automated pipelines |
| **Difficulty** | ⭐ (1–2 days) | ⭐⭐⭐ (1–2 weeks) | ⭐⭐⭐⭐⭐ (1–2 months) |
| **GPU needed?** | No | No | Optional (LSTM only) |
| **Outcome** | A notebook with a few charts | A modular, tested, documented pipeline + dashboard | Research-grade system |
| **GitHub proof value** | Low — looks like a tutorial | **High — looks like industry work, still explainable** | Very high but risky to finish |

**Best for a student who wants strong GitHub proof quickly: Option B.** It shows statistics, ML, forecasting, software engineering and communication — and every part can be explained in an interview without hand-waving.

## C. Selected approach — Option B

- **Pandas/NumPy** for data, **SciPy** for regression and Theil–Sen, a **hand-written Mann-Kendall** (shows you understand it), **statsmodels** for STL and SARIMA, **scikit-learn** for Isolation Forest and regression, **Matplotlib/Seaborn** for static figures, **Plotly + Streamlit** for the dashboard, **pytest** for tests.
- **Virtual simulation** as the default data source, **NASA POWER** as a one-command switch to real data.
- **Modular `src/` package** + `main.py` orchestrator + notebook for storytelling.

---

## D. Architecture

### D1. Block diagram
```
INPUT                    PROCESSING                                     OUTPUT
─────                    ──────────                                     ──────
                    ┌───────────────┐
Simulation ────────►│  data_loader  │ validate schema
   or               └──────┬────────┘
NASA POWER CSV             ▼
                    ┌───────────────┐
                    │ preprocessing │──────────────────────────► data_quality_report.csv
                    └──────┬────────┘
                           ▼
                    ┌───────────────┐                              climate_features.csv
                    │   features    │──────────────────────────► climate_monthly.csv
                    └──────┬────────┘                              climate_yearly.csv
          ┌────────────┬───┴────────┬─────────────┐
          ▼            ▼            ▼             ▼
       ┌─────┐    ┌────────┐   ┌─────────┐   ┌──────────┐
       │ EDA │    │ Trend  │   │ Anomaly │   │ Forecast │──────► figures 01–19
       └──┬──┘    └───┬────┘   └────┬────┘   └────┬─────┘        tables (15 CSVs)
          └───────────┴──────┬──────┴─────────────┘               models/sarima_*.pkl
                             ▼
                      ┌─────────────┐
                      │   Report    │─────────────────────────► climate_insights_report.md
                      └──────┬──────┘                              key_insights.csv
                             ▼
                      ┌─────────────┐
                      │  Dashboard  │─────────────────────────► http://localhost:8501
                      └─────────────┘
```

### D2. Module-by-module
| Module | Input | Does | Output |
|---|---|---|---|
| **Input data** | — | Simulated daily climate or real CSV in schema `date, city, temp_mean, temp_max, temp_min, rainfall_mm, humidity_pct` | `data/raw/climate_data_raw.csv` |
| **Data cleaning** (`preprocessing.py`) | raw CSV | parse dates → drop duplicates → sentinel codes → range checks → min/max consistency → full daily calendar → interpolation (≤7 days) / climatology fill | clean CSV + quality report |
| **Feature engineering** | clean data | calendar, IMD seasons, 1991–2020 smoothed daily normal, anomaly, de-trended residual, monthly-std z-score, hot days (> p90 Tmax), cold nights, rainy/heavy-rain days, rolling sums | daily / monthly / yearly tables |
| **Exploratory analysis** (`eda.py`) | daily features | descriptive stats, missing-value chart, distributions, seasonal cycle, correlation, season box plots | figures 01–05 |
| **Trend analysis** | yearly + monthly | OLS slope & p, Mann-Kendall τ/Z/p, Sen's slope, decade comparison, seasonal warming rates, STL | `trend_summary.csv`, figures 06–13 |
| **Anomaly detection** | daily + monthly | |z| > 3 days → merged events with severity; wet-day p99.5 rain; Isolation Forest months; recall/precision vs ground truth | event tables, figures 14–16 |
| **Forecasting** | monthly temp | back-test 3 models on 36 held-out months; refit best; 60-month forecast with 95 % interval | metrics, forecast tables, figures 17–19 |
| **Reporting** | all tables | auto-written insights + markdown report | `reports/`, `key_insights.csv` |
| **Dashboard** | processed data + tables | city/year filters, KPIs, 5 tabs | Streamlit app |

### D3. Data flow
`raw CSV` → (clean) → `climate_data_clean.csv` → (features) → `climate_features.csv` (daily) ➜ aggregated into `climate_monthly.csv` and `climate_yearly.csv`. **EDA** and **anomaly z-scores** use daily data; **trend tests** use yearly data (removes seasonality and autocorrelation); **Isolation Forest** and **forecasting** use monthly data. Every analysis writes CSV tables, which the **report** and **dashboard** read — so the dashboard never recomputes anything.

---

## E. Implementation phases

| Phase | What to do | Why | Expected output | Common beginner mistakes | How to verify |
|---|---|---|---|---|---|
| **1 Environment setup** | Install Python 3.10–3.13, Git, VS Code; create venv; install requirements | Isolated, reproducible environment | `(venv)` in prompt | Installing globally; forgetting to activate venv | `python -c "import statsmodels"` works |
| **2 Project structure** | Create folders (section F), `config.py`, `utils.py`, `.gitignore` | Professional layout; no hard-coded paths | Folder tree | Everything in one notebook; absolute paths like `C:\Users\...` | `tree` / file explorer matches section F |
| **3 Dataset loading** | Generate simulation (`--step generate`) or download NASA data; load with schema check | Need data in a known format | `climate_data_raw.csv` (51,286 rows) | Wrong working directory; wrong column names | Loader logs rows × columns, no error |
| **4 Cleaning & preprocessing** | Run `--step clean` | Garbage in = garbage out | Clean CSV, 0 missing cells, quality report | Dropping all rows with NaN; interpolating rainfall; forgetting duplicates | Quality report shows duplicates removed = 150, missing after = 0 |
| **5 EDA** | `--step eda`; study charts | Understand seasonality and ranges before modelling | Figures 01–05, descriptive stats | Skipping EDA; plotting 51k points per city unreadably | Seasonal chart shows monsoon peak in Jun–Sep (Chennai Oct–Nov) |
| **6 Feature engineering** | Normals, anomalies, z-scores, seasons, indicators | Raw temperature is dominated by season; anomalies reveal climate signal | 23-column daily table + monthly + yearly | Computing anomaly vs whole-period mean (mixes in the trend); leap-day bugs | Mean anomaly over 1991–2020 ≈ 0 |
| **7 Trend analysis** | `--step trend` | Quantify change with significance | `trend_summary.csv`, figures 06–13 | Trend on daily data (autocorrelated → fake significance); reporting slope without p-value | Recovered slopes ≈ injected (e.g. Delhi 0.32 vs 0.30) |
| **8 Anomaly detection** | `--step anomaly` | Find extreme events | Event tables, evaluation table | Not de-trending (recent years all "anomalous"); one global threshold for all seasons | Heatwave recall > 90 % |
| **9 Forecasting** | `--step forecast` | Estimate near-future climate and its uncertainty | Metrics, forecasts, figures 17–19 | No baseline; testing on training data; random train/test split on time series | Best model RMSE < seasonal naive RMSE |
| **10 Visualisation & insights** | `--step report`; open dashboard | Communicate | Report, dashboard | Charts without titles/units; no conclusions | Report has ≥ 15 insights; dashboard tabs all load |
| **11 Testing** | `pytest -v` | Prove correctness | 6 tests pass | No tests at all | `6 passed` |
| **12 GitHub publishing** | See `02_GITHUB_AND_PROOF_GUIDE.md` | Public proof | Public repo with README images | Committing venv/big CSVs; one giant commit | README renders with images on GitHub |
| **13 Resume / explanation** | See `03_CAREER_KIT.md` | Convert work into opportunities | Resume bullets, LinkedIn post | Vague bullets without numbers | Each bullet has a metric |

---

## F. Folder structure (purpose of each item)

| Path | Purpose |
|---|---|
| `main.py` | Single entry point; runs all steps or one step (`--step`) and supports real data (`--source external`) |
| `requirements.txt` | Library list for `pip install -r` |
| `pytest.ini` | Lets tests import `src` and silences library warnings |
| `.gitignore` | Keeps venv, large CSVs, caches and secrets out of Git |
| `README.md` | Recruiter-facing project page |
| `src/` | All reusable logic, one module per pipeline stage |
| `src/config.py` | Paths, city profiles, thresholds — the only place to change settings |
| `src/utils.py` | Logger, plot style, figure/table save helpers, step timer |
| `app/streamlit_app.py` | Interactive dashboard |
| `notebooks/` | Storytelling walkthrough (calls `src/` functions — no duplicated logic) |
| `tests/` | Automated unit tests |
| `data/raw/` | Raw generated data + `injected_events.csv` ground truth |
| `data/processed/` | Clean data and engineered features |
| `data/external/` | Real public datasets you download |
| `outputs/figures/` | All PNG charts (committed — recruiters see them) |
| `outputs/tables/` | All CSV results |
| `models/` | Saved fitted models (git-ignored, re-created) |
| `reports/` | Auto-generated insights report |
| `images/screenshots/` | Your manual screenshots & GIF for README |
| `docs/` | Guides (this file, GitHub, career, troubleshooting, roadmap) |

---

## G. Installation and environment setup

**Python version:** 3.10, 3.11, 3.12 or 3.13 (tested on 3.13). Download from python.org — on Windows tick **"Add python.exe to PATH"**.

### Windows (PowerShell)
```powershell
python --version
cd path\to\Climate-Trend-Analyzer
python -m venv venv
venv\Scripts\activate
# if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS / Linux
```bash
python3 --version
cd path/to/Climate-Trend-Analyzer
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Installing libraries one by one (if you start from scratch without requirements.txt)
```bash
pip install pandas numpy matplotlib seaborn plotly scipy scikit-learn statsmodels streamlit requests ipykernel pytest
```

### Generating requirements.txt yourself
```bash
pip freeze > requirements-lock.txt
```
`pip freeze` lists *every* package with exact versions (good for exact reproduction). The provided `requirements.txt` lists only top-level packages with minimum versions — easier to read and install across machines.

### Check the installation worked
```bash
python -c "import pandas, numpy, matplotlib, seaborn, plotly, scipy, sklearn, statsmodels, streamlit; print('All libraries OK')"
pip list
```
Deactivate the venv any time with `deactivate`.

---

## H. Full code — file-by-file guide

Every file contains detailed comments; open them alongside this table. The code is complete and executable.

| File | What it does | Key ideas to explain in interviews |
|---|---|---|
| `src/config.py` | Central settings: paths, 4 city climate profiles (mean temp, seasonal amplitude, warming rate, monsoon timing, rainfall, humidity), data-quality injection rates, analysis thresholds | Config-driven design; WMO 1991–2020 baseline |
| `src/utils.py` | Logger (UTF-8 safe on Windows), plot style, `save_figure`, `save_table`, `timed` context manager | DRY helpers; non-GUI `Agg` backend |
| `src/data_generator.py` | Builds the virtual climate: seasonal cosine + linear warming + AR(1) noise; monsoon-shaped wet-day probability × Gamma rainfall; humidity linked to rain & heat; injects heatwaves, cold spells, cloudbursts; corrupts data (NaN, -999, outage, duplicates, shuffle) | Why AR(1) (weather persistence); why Gamma (skewed rainfall); ground truth for evaluation |
| `src/fetch_nasa_power.py` | Downloads real daily T2M, T2M_MAX, T2M_MIN, PRECTOTCORR, RH2M per city from NASA POWER API into our schema | Real-data path; -999 missing code |
| `src/data_loader.py` | Loads raw CSV, validates schema; helper to map any external CSV to our columns | Fail-fast validation |
| `src/preprocessing.py` | 7-step cleaning with an auditable data-quality report | Interpolation for smooth variables vs climatology fill for rainfall |
| `src/feature_engineering.py` | IMD seasons; smoothed daily climatology; anomaly; de-trended residual; monthly-std z-score; p90/p10 extremes; rolling sums; monthly & yearly aggregates | Why de-trend before anomaly detection |
| `src/eda.py` | Descriptive stats and figures 01–05 | Twin-axis climatology chart |
| `src/trend_analysis.py` | Mann-Kendall (with tie correction), Sen's slope, OLS; trend table for 9 indicators × 4 cities; decadal & seasonal tables; figures 06–13 (incl. warming stripes, STL) | Parametric vs non-parametric tests |
| `src/anomaly_detection.py` | Z-score day flags → merged events with severity; rainfall p99.5; Isolation Forest on monthly features; evaluation vs ground truth; figures 14–16 | Event-level recall vs day-level precision |
| `src/forecasting.py` | Seasonal naive, linear trend + month dummies, SARIMA(1,0,1)(0,1,1,12) with drift; 36-month back-test; best model refit; 60-month forecast with 95 % interval; figures 17–19 | Time-ordered hold-out; baseline comparison |
| `src/report_generator.py` | Reads all tables, writes data-driven insight sentences and a markdown report | Automated reporting |
| `main.py` | CLI orchestrator with `--step`, `--source`, `--input` | Reproducibility |
| `app/streamlit_app.py` | Dashboard: city & year filters, KPI cards, Trends / Seasonality / Anomalies / Forecast / Insights tabs | Cached data loading |
| `tests/test_pipeline.py` | 6 tests: simulation validity, AR(1) autocorrelation, cleaning, Mann-Kendall, Sen's slope, anomaly detection | Testing statistical code with known answers |
| `notebooks/climate_trend_analysis.ipynb` | Step-by-step narrative calling the `src` modules; compares estimated vs injected warming | Notebook for story, modules for logic |

**Simplified first version (if the full version feels heavy):** start with `data_generator.py` → `preprocessing.py` → yearly means + `scipy.stats.linregress` → one trend chart. Then upgrade in this order: Mann-Kendall/Sen → z-score anomalies → Isolation Forest → SARIMA → dashboard.

---

## I. Virtual simulation — how it works

### I1. Representing the variables
| Variable | Representation |
|---|---|
| **Dates** | `pd.date_range("1990-01-01", "2024-12-31", freq="D")` → 12,784 days per city; `day_of_year` drives seasonality |
| **Temperature** | `T = mean + A·cos(2π(doy − peak)/365.25) + trend·years + AR(1) noise` |
| **Rainfall** | `P(rain today) = 0.04 + 0.78·monsoon_curve(doy)`; amount ~ `Gamma(shape=0.75, scale)` scaled to the city's annual total; +1.5 % intensity per decade |
| **Humidity** | `mean + 18·(monsoon − avg) + 8·rainy_day − 1.2·temp_anomaly + noise`, clipped to 8–100 % |
| **Seasons** | IMD: Winter (Dec–Feb), Pre-Monsoon (Mar–May), Monsoon (Jun–Sep), Post-Monsoon (Oct–Nov) |

### I2. Climate variation & seasonal trends
- **Seasonal cycle:** cosine with city-specific amplitude (Delhi ±9.5 °C, Mumbai ±2.8 °C) and peak day (Delhi late May, Bengaluru mid-April).
- **Monsoon:** circular Gaussian rain-probability curve centred on each city's peak (Chennai in November = north-east monsoon).
- **Weather noise:** AR(1) with φ = 0.7 — hot days cluster, as in reality.
- **Long-term trend:** linear warming of 0.20–0.30 °C/decade per city.

### I3. Abnormal values
- **Heatwaves:** 12 per city, 3–7 days, +5.5 to +8 °C, rain suppressed.
- **Cold spells:** 8 per city, 3–6 days, −5 to −7 °C, in the cool season.
- **Extreme rain:** 15 per city, single days of 12–25 % of annual rainfall.
- **Sensor problems:** 2 % NaN, 0.1 % −999/999 codes, a 20-day outage, 150 duplicates.

### I4. Long-term trend analysis
Yearly means remove the seasonal cycle and most autocorrelation. Mann-Kendall tests whether later years are systematically higher; Sen's slope estimates the rate; OLS gives a comparable parametric slope and R². Because the true rate is known, compare estimated vs injected (notebook cell "Did we recover the warming rate?").

### I5. Anomaly identification
1. Daily normal = mean of each day-of-year over 1991–2020, smoothed with a 31-day circular window.
2. Anomaly = observed − normal. Residual = anomaly − fitted linear trend.
3. z = residual / std(residual for that month). |z| > 3 → anomaly; consecutive days → one event.
4. Rainfall: wet-day 99.5th percentile threshold. Months: Isolation Forest on (temp anomaly, rain departure, humidity departure).
5. Compare with `injected_events.csv` for recall and precision.

### I6. Step-by-step simulation workflow
| Step | Command / action | Result |
|---|---|---|
| 1 | Activate venv | `(venv)` prompt |
| 2 | `python main.py --step generate` | `data/raw/climate_data_raw.csv` (51,286 rows), `injected_events.csv` (140 events) |
| 3 | Open the raw CSV, screenshot first rows | Proof: dataset preview |
| 4 | `python main.py --step clean` | Clean + feature files; quality report in terminal |
| 5 | `python main.py --step eda` | Figures 01–05 |
| 6 | `python main.py --step trend` | Warming rates printed; figures 06–13 |
| 7 | `python main.py --step anomaly` | Recall/precision printed; figures 14–16 |
| 8 | `python main.py --step forecast` | Best model per city; figures 17–19 |
| 9 | `python main.py --step report` | `reports/climate_insights_report.md` |
| 10 | `pytest -v` | 6 passed |
| 11 | `streamlit run app/streamlit_app.py` | Dashboard in browser |
| 12 | Capture screenshots/GIF, commit, push | GitHub proof |

**Proof assets:** see `02_GITHUB_AND_PROOF_GUIDE.md` section M for the exact list of screenshots, graphs, tables and recordings.

---

## J. How to run (exact commands and expected output)

```bash
# from the project root, venv activated
python main.py                        # everything, ~2 minutes
python main.py --step trend           # one step only (needs earlier steps done once)
pytest -v
streamlit run app/streamlit_app.py    # opens http://localhost:8501
jupyter notebook notebooks/climate_trend_analysis.ipynb   # needs: pip install notebook
```

### Sample terminal output (abridged, real run)
```
12:31:51 | INFO | src.data_generator  | Saved raw data -> data/raw/climate_data_raw.csv (51286 rows)
12:31:51 | INFO | src.data_generator  | Saved ground-truth events -> data/raw/injected_events.csv (140 events)
12:31:52 | INFO | src.preprocessing   |   duplicate_rows_removed              150
12:31:52 | INFO | src.preprocessing   |   sentinel_values_replaced            268
12:31:52 | INFO | src.preprocessing   |   missing_cells_after_imputation      0
12:32:09 | INFO | src.trend_analysis  |   Delhi      warming +0.32 °C/decade | MK p=0.0000 | increasing
12:32:09 | INFO | src.trend_analysis  |   Mumbai     warming +0.18 °C/decade | MK p=0.0000 | increasing
12:32:31 | INFO | src.anomaly_detection | heatwave      recall 98% (47/48 events) | day precision 84%
12:32:31 | INFO | src.anomaly_detection | extreme_rain  recall 85% (51/60 events) | day precision 90%
12:33:37 | INFO | src.forecasting     |   Delhi      best model: SARIMA (RMSE 0.735 °C)
12:33:50 | INFO | pipeline            | PIPELINE COMPLETE
```
A full log of a real run is saved in `outputs/pipeline_run_log.txt`.

### What success looks like
- Terminal ends with **PIPELINE COMPLETE**, no tracebacks.
- `outputs/figures/` has **19 PNGs**, `outputs/tables/` has **15 CSVs**, `reports/climate_insights_report.md` exists.
- `pytest` shows **6 passed**. Dashboard tabs load for every city.

### Sample trend-analysis interpretation
> "Delhi's annual mean temperature rose at +0.32 °C per decade (Sen's slope; Mann-Kendall p < 0.001), about +0.74 °C between the 1990s and the last decade. Hot days (Tmax above the 1991–2020 90th percentile) increased from ~27 to ~48 per year. Annual rainfall shows no significant trend (p = 0.48)."

### Sample anomaly table (`temperature_anomaly_events.csv`, top rows)
| city | type | start_date | end_date | duration_days | peak_temp | peak_zscore | severity |
|---|---|---|---|---|---|---|---|
| Bengaluru | hot_anomaly | 1996-03-25 | 1996-04-03 | 10 | 38.62 | 10.74 | Extreme |
| Chennai | cold_anomaly | 2021-12-27 | 2021-12-31 | 5 | 20.99 | −9.22 | Extreme |
| Mumbai | hot_anomaly | 2003-06-15 | 2003-06-20 | 6 | 39.89 | 7.80 | Extreme |

### Sample summary table (`decadal_comparison.csv`, Bengaluru)
| decade | avg_temp °C | hot_days/yr | avg annual rainfall mm |
|---|---|---|---|
| 1990s | 24.01 | 24.7 | 1038 |
| 2000s | 24.13 | 30.3 | 1068 |
| 2010s | 24.48 | 47.4 | 960 |
| 2020s | 24.65 | 62.6 | 1074 |

### Expected graphs
Warming trend lines rising for all cities (06); warming stripes shifting from blue to red (08); rainfall bars with no clear direction (07); red/blue anomaly dots scattered across all decades (14); forecasts continuing the seasonal wave with a slight upward drift and shaded uncertainty (18).
