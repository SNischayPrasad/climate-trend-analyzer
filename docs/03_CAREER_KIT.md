# 💼 Career Kit — Resume, LinkedIn & Interview Preparation

Section **N** of the deliverables. All numbers below come from the actual pipeline output — if you change the simulation seed or use real data, update them from `outputs/tables/`.

> **Honesty rule:** always say the data is *simulated* (or name the real source if you switch to NASA POWER). Interviewers respect "I built a simulation with known ground truth so I could validate my methods" — it's a genuine strength. Never present simulated numbers as real Indian climate findings.

---

## 1. Resume bullet points (pick 2–3)

**Data Scientist / ML version**
- Built an end-to-end **climate analytics pipeline in Python** (pandas, statsmodels, scikit-learn) processing **51K+ daily records across 4 cities (1990–2024)**; detected significant warming of **+0.18 to +0.32 °C/decade** using Mann-Kendall and Sen's slope tests (p < 0.001).
- Implemented **Z-score and Isolation Forest anomaly detection** on de-trended temperature anomalies, recovering **98 % of injected heatwaves** and **85 % of extreme-rainfall events** validated against simulation ground truth.
- Back-tested **SARIMA vs. linear-regression vs. seasonal-naive** forecasts on a 3-year hold-out, cutting monthly temperature RMSE by **26–42 %** vs. baseline (best RMSE 0.37 °C); delivered results via a **Streamlit dashboard** and auto-generated report.

**Data Analyst / Business Analyst version**
- Cleaned and validated **51K+ climate records** (duplicates, sensor error codes, 5K+ missing values) with an auditable data-quality report, producing an analysis-ready dataset with **0 missing values**.
- Analysed 35 years of temperature and rainfall trends for 4 cities, finding **hot days per year roughly doubled** while annual rainfall showed no significant trend; translated findings into recommendations for heat-action and drainage planning.
- Built an interactive **Streamlit + Plotly dashboard** with KPI cards, seasonal heatmaps, anomaly tables and 5-year forecasts for non-technical stakeholders.

**Research / Environmental Analyst version**
- Developed a reproducible climate-trend framework using **WMO 1991–2020 climate normals**, Mann-Kendall/Sen's slope trend tests and **STL decomposition**; validated method accuracy on a physically-motivated simulation (estimated vs. injected warming within ±0.04 °C/decade).

**Project line for the resume header:**
`Climate Trend Analyzer | Python, pandas, statsmodels, scikit-learn, Streamlit | github.com/SNischayPrasad/climate-trend-analyzer`

---

## 2. LinkedIn project descriptions

### Version 1 — Launch post (storytelling)
> 🌡️ **Is my city getting hotter? I built a tool to find out — with statistics, not guesses.**
>
> Over the last week I built **Climate Trend Analyzer**, an end-to-end Python pipeline that analyses 35 years of daily climate data for Delhi, Mumbai, Chennai and Bengaluru.
>
> Since I don't have access to institutional climate databases, I built a **virtual simulation** with realistic seasons, monsoons, a warming trend and injected heatwaves — which meant I could *check* whether my methods actually find the truth.
>
> What it does:
> ✅ Cleans messy sensor data (duplicates, -999 error codes, gaps)
> ✅ Tests long-term trends with Mann-Kendall & Sen's slope → +0.18 to +0.32 °C/decade, all significant
> ✅ Detects anomalies with Z-scores and Isolation Forest → 98 % of injected heatwaves caught
> ✅ Forecasts monthly temperature (SARIMA vs regression vs baseline)
> ✅ Interactive Streamlit dashboard + auto-generated insights report
>
> Biggest lesson: **de-trend before you detect anomalies** — otherwise every recent year looks "abnormal".
>
> 🔗 Code: github.com/SNischayPrasad/climate-trend-analyzer
> #DataScience #ClimateData #Python #TimeSeries #MachineLearning #Streamlit #OpenToWork

### Version 2 — Short (Projects section of your profile)
> **Climate Trend Analyzer** — Python pipeline for long-term climate analysis of 4 Indian cities (1990–2024). Data cleaning, climate normals & anomalies, Mann-Kendall/Sen's slope trend tests, Z-score + Isolation Forest anomaly detection validated against ground truth, back-tested SARIMA forecasting, and a Streamlit dashboard. Skills: pandas, statsmodels, scikit-learn, Plotly, Streamlit, pytest.

### Version 3 — Technical deep-dive post
> 📊 **3 things I learned building a climate trend analyzer**
>
> 1️⃣ **Trend tests on daily data lie.** Daily temperatures are autocorrelated, so p-values look far more significant than they are. Aggregating to yearly means before running Mann-Kendall fixed that.
> 2️⃣ **Your baseline model matters.** A "next January = last January" forecast was surprisingly hard to beat — SARIMA and a trend-plus-seasonality regression beat it by 26–42 % RMSE, and in 3 of 4 cities the simple regression tied or beat SARIMA.
> 3️⃣ **Simulated data with ground truth is a superpower.** Because I injected 140 extreme events, I could measure recall (98 % heatwaves) and precision (84 %) instead of just eyeballing charts.
>
> Full code, charts and docs: github.com/SNischayPrasad/climate-trend-analyzer
> #TimeSeries #Statistics #DataScience #ClimateTech

---

## 3. Interview questions & strong answers

**Q1. Walk me through your project.**
> "It's an end-to-end climate analytics pipeline. Input is daily temperature, rainfall and humidity for four Indian cities from 1990 to 2024 — simulated, because I didn't have institutional data, but built from realistic components so I'd have ground truth. The pipeline cleans the data and logs every fix, computes 1991–2020 climate normals and anomalies, tests long-term trends with Mann-Kendall and Sen's slope, detects anomalies with Z-scores and an Isolation Forest, back-tests three forecasting models, and auto-generates a report and a Streamlit dashboard. Key result: all four cities warm significantly, 0.18–0.32 °C per decade, hot days roughly doubled, and I caught 98 % of injected heatwaves."

**Q2. Why did you use simulated data? Isn't that a weakness?**
> "It was a deliberate choice. With real data you never know the true answer, so you can't measure whether your method works. My simulation includes seasonality, autocorrelated weather, a monsoon, a known warming rate and 140 known extreme events, plus realistic data problems. I recovered the warming rate within about 0.04 °C per decade and measured detection recall and precision. And the pipeline already has a NASA POWER downloader, so switching to real data is one command — the simulation validated the methods first."

**Q3. Why Mann-Kendall instead of just linear regression?**
> "Linear regression assumes normally distributed residuals and is sensitive to outliers — one freak hot year can tilt the slope. Mann-Kendall is non-parametric: it only asks whether later values tend to be larger than earlier ones, so it's robust to outliers and skewed data. It gives significance but not magnitude, so I pair it with Sen's slope — the median of all pairwise slopes. I still report OLS for comparison; when both agree I'm more confident. This trio is standard in hydrology and IPCC-style reports."

**Q4. How did you detect anomalies, and why de-trend first?**
> "First I compute a 'normal' for each day of the year from the 1991–2020 baseline and subtract it — that removes the seasonal cycle. But the climate is warming, so recent years would all look abnormally hot if I stopped there. I fit and remove the long-term linear trend, standardise by each month's variability, and flag |z| > 3. Consecutive flagged days merge into an event with a severity label. For rainfall, which is very skewed, a z-score doesn't fit, so I use the city's 99.5th percentile of wet-day rainfall. Then an Isolation Forest finds months where the *combination* of temperature, rainfall and humidity is unusual."

**Q5. How did you evaluate the anomaly detection?**
> "Two metrics against the injected events. Event-level recall: was each injected heatwave flagged on at least one day? 47 of 48 were — 98 %. Day-level precision: of all days flagged hot, how many fall inside an injected event (±1 day)? About 84 %. The rest are natural extremes from the noise process — which in real life would be genuine anomalies too, so precision is a conservative estimate. Raising the threshold to 3.5 trades recall for precision."

**Q6. Explain your forecasting approach and results.**
> "I aggregate to monthly mean temperature and hold out the last 36 months — always a time-ordered split, never random, because that would leak the future. I compare three models: a seasonal-naive baseline, a linear regression with a time trend plus month dummies, and SARIMA(1,0,1)(0,1,1,12) with drift. The best reached RMSE 0.37–0.74 °C, 26–42 % better than the baseline. Interestingly the simple regression tied or beat SARIMA in three cities — when the data is mostly trend plus a stable season, a simpler model is enough. I refit the winner on all data and forecast five years with 95 % intervals."

**Q7. What was the hardest data-cleaning issue?**
> "Deciding how to fill gaps differently for each variable. Temperature and humidity change smoothly, so time interpolation works for gaps up to seven days. Rainfall is intermittent — interpolating between a 40 mm day and a dry day invents rain that never fell. So for rainfall, and for long outages, I filled with the day-of-year median. I also had -999 sensor codes that would destroy averages if not caught, duplicates from double uploads, and a 20-day outage. Every fix is counted in a data-quality report."

**Q8. What is a climate normal and why 1991–2020?**
> "A climate normal is the 30-year average used as the reference for 'normal' conditions. The WMO currently recommends 1991–2020. Thirty years is long enough to average out year-to-year variability like El Niño. I computed a normal for each day of the year, smoothed with a 31-day window so a single odd year doesn't create bumps."

**Q9. How would this scale to real-world or production use?**
> "Swap the simulation for NASA POWER, IMD gridded data or ERA5 — the loader already maps external columns to my schema. For more locations I'd process cities in parallel and store data in Parquet or a database. I'd schedule the pipeline monthly with GitHub Actions or Airflow, add data-validation checks, and deploy the dashboard. Statistically I'd add autocorrelation-corrected Mann-Kendall and extreme-value analysis for return periods."

**Q10. What business value does this deliver?**
> "It turns 51,000 noisy records into a few defensible numbers decision-makers can act on: how fast each city is warming, how much more often extreme heat occurs, and whether rainfall is changing. A city planner could prioritise heat-action plans in the fastest-warming city; a drainage authority learns to design for extreme single days rather than annual averages; a health department could use the anomaly detector as a heatwave early-warning trigger. Insurers and ESG teams use the same analysis for physical-risk scoring."

**Bonus quick-fire questions**
- *What is a p-value?* — The probability of seeing a trend at least this strong if there were truly no trend. p < 0.05 → we reject "no trend".
- *What is STL?* — Seasonal-Trend decomposition using LOESS: splits a series into trend + seasonal + residual.
- *Why AR(1) noise?* — Weather is persistent: a hot day is likely followed by another. White noise would underestimate heatwave clustering.
- *Why Isolation Forest?* — Unsupervised, fast, multivariate; isolates rare points with fewer random splits.

---

## 4. Explaining to HR (simple, 30 seconds)
> "I built a tool that looks at 35 years of daily weather for four Indian cities and answers: is it getting hotter, are extreme events happening more often, and what can we expect next? It found all four cities are warming and very hot days have roughly doubled. The results are shown in an interactive dashboard so non-technical people can explore them. It shows I can take messy data, analyse it properly and explain the results clearly — which is what a data analyst does every day."

## 5. Explaining to a technical interviewer (2 minutes)
1. **Architecture:** modular `src/` package, config-driven, `main.py` CLI, logging, pytest, Streamlit front end.
2. **Data:** physically-motivated simulation (seasonal cosine, AR(1), Gamma rainfall, injected events) with realistic corruption → ground truth for validation; NASA POWER loader for real data.
3. **Cleaning:** sentinel codes, range checks, calendar re-indexing, variable-specific imputation, auditable report.
4. **Features:** smoothed day-of-year climatology (1991–2020), anomalies, de-trended residual, month-standardised z-score, percentile-based extreme indices.
5. **Methods:** OLS + Mann-Kendall + Sen's slope on yearly series; STL; Z-score/percentile/Isolation Forest; SARIMA vs regression vs naive with time-ordered hold-out.
6. **Validation:** recovered warming rates; recall/precision vs injected events; RMSE vs baseline.
7. **Limitations & next steps:** autocorrelation-corrected MK, GEV return periods, real-data validation.

## 6. Explaining real-world value confidently
- Lead with the **decision** the analysis supports, not the algorithm: "This tells a city where to invest in heat resilience first."
- Quote **one number per claim**: "+0.32 °C per decade, p < 0.001".
- Acknowledge the limitation **before** they ask: "It's validated on simulation with known ground truth; the next step is running it on NASA POWER data — the code already supports it."
- Connect to the employer: for an insurer → physical-risk scoring; for consulting → ESG climate disclosure; for government/analytics → heat-action planning; for agritech → seasonal shifts and rainfall risk.
