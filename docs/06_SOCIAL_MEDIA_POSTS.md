# 📣 Social Media Posts — LinkedIn & Instagram

Copy-paste-ready captions plus which image to attach to each post. All images were generated from a real run of this project:

| Asset | File |
|---|---|
| LinkedIn post image (1200×627) | `images/social/linkedin_cover.png` |
| Instagram carousel, 7 slides (1080×1350) | `images/social/instagram_01.png` … `instagram_07.png` |
| Dashboard screenshots | `images/screenshots/05_dashboard_trends.png`, `06_dashboard_anomalies.png`, `07_dashboard_forecast.png`, `08_dashboard_insights.png`, `12_dashboard_seasonality.png`, `13_dashboard_mumbai.png` |
| Terminal screenshots | `images/screenshots/03_pipeline_run.png`, `04_tests_passing.png` |
| Demo GIF (≈ 13 s, 0.4 MB) | `images/demo.gif` |

Regenerate everything after any change with:
```bash
python main.py
python scripts/capture_screenshots.py
python scripts/make_social_images.py
```

**GitHub URL used below:** `https://github.com/SNischayPrasad/climate-trend-analyzer`. It only works once the repository has been created and pushed (see `02_GITHUB_AND_PROOF_GUIDE.md`).

> **Stay honest:** every caption says the data is simulated. That protects your credibility, and "I validated my methods against known ground truth" is a strong talking point.

---

## LinkedIn

### Post 1: Launch post (recommended first post)
**Attach:** a document/carousel made of `instagram_01` to `instagram_07` (LinkedIn → *Add a document* → upload them as a PDF), **or** a single image: `linkedin_cover.png`. Put the GitHub link in the **first comment** as well; LinkedIn shows posts without links in the body to more people.

```
🌡️ Is my city actually getting hotter? I built a tool to answer that with statistics, not guesses.

Meet Climate Trend Analyzer, an end-to-end Python project that analyses 35 years (1990–2024) of daily climate data for Delhi, Mumbai, Chennai and Bengaluru.

I don't have access to government climate databases, so I built a realistic virtual simulation: seasons, monsoons, a long-term warming trend, 140 hidden extreme events and messy sensor errors. Because I knew the "true answer", I could measure whether my methods actually find it.

What the pipeline does:
✅ Cleans 51K+ records (duplicates, -999 sensor codes, missing values)
✅ Builds 1991–2020 climate normals and daily anomalies
✅ Tests long-term trends with Mann-Kendall + Sen's slope → +0.18 to +0.32 °C per decade, significant in all 4 cities
✅ Detects heatwaves, cold spells and extreme rain with Z-scores + Isolation Forest → 98% of hidden heatwaves caught
✅ Back-tests 3 forecasting models (SARIMA, regression, naive baseline) → 26–42% lower error than the baseline
✅ Interactive Streamlit dashboard + an auto-generated insights report

💡 Biggest lesson: remove the long-term trend before hunting for anomalies. Otherwise every recent year looks "abnormal".

Next step: running the same pipeline on real NASA POWER satellite data (the downloader is already built).

🔗 Code, charts and docs: https://github.com/SNischayPrasad/climate-trend-analyzer

I'd love feedback from anyone working in climate, environmental data or time-series analytics! 🙌

#DataScience #Python #ClimateData #TimeSeries #MachineLearning #DataAnalytics #Streamlit #ClimateChange #OpenToWork #StudentProjects
```

**First comment:**
```
📂 GitHub repo: https://github.com/SNischayPrasad/climate-trend-analyzer
Tech stack: pandas · NumPy · SciPy · statsmodels · scikit-learn · Plotly · Streamlit · pytest
```

### Post 2: Short version (also for the Featured / Projects section)
**Attach:** `linkedin_cover.png`

```
📊 New project: Climate Trend Analyzer

A Python pipeline that analyses 35 years of daily climate data (simulated, with known ground truth) for 4 Indian cities:
• Data cleaning with an auditable quality report
• Mann-Kendall & Sen's slope trend tests → +0.18 to +0.32 °C/decade
• Z-score + Isolation Forest anomaly detection → 98% heatwave recall
• SARIMA vs regression forecasting, back-tested on 3 held-out years
• Interactive Streamlit dashboard

🔗 https://github.com/SNischayPrasad/climate-trend-analyzer

#DataScience #Python #ClimateData #MachineLearning
```

### Post 3: Lessons learned (post about a week after Post 1)
**Attach:** `images/screenshots/07_dashboard_forecast.png` or `outputs/figures/19_model_comparison.png`

```
3 things I learned building a climate trend analyzer 👇

1️⃣ Trend tests on daily data lie.
Daily temperatures are autocorrelated (a hot day is usually followed by another), which inflates significance. Aggregating to yearly averages before running the Mann-Kendall test fixed it.

2️⃣ Always beat a dumb baseline first.
"Next January = last January" was surprisingly hard to beat. SARIMA and a simple trend + seasonality regression beat it by 26–42%, and in 3 of 4 cities the simple regression edged out SARIMA. Simpler often wins.

3️⃣ Simulated data with ground truth is a superpower.
I hid 140 extreme events in the data, so instead of eyeballing charts I could measure recall (98% of heatwaves) and precision (84%).

Full code + docs: https://github.com/SNischayPrasad/climate-trend-analyzer

What's your go-to method for detecting trends in noisy time series?

#TimeSeries #Statistics #DataScience #Python #LearningInPublic
```

### Post 4: Dashboard demo (video)
**Attach:** a 30–60 s screen recording of the dashboard. `images/demo.gif` works as a preview, but LinkedIn shows MP4 video better. Record with Xbox Game Bar (`Win + G`) or OBS.

```
🎥 Quick demo of my Climate Trend Analyzer dashboard.

Pick a city → see its warming rate, hot-day trend, a monthly anomaly heatmap, every detected heatwave and cold spell, and a 5-year temperature forecast with uncertainty bands.

Built with Python, Plotly and Streamlit on top of a fully tested analysis pipeline.

🔗 https://github.com/SNischayPrasad/climate-trend-analyzer

#Streamlit #DataVisualization #Python #ClimateData #Dashboard
```

---

## Instagram

**Format:** carousel post. Upload `images/social/instagram_01.png` → `instagram_07.png` in order (4:5 portrait, which takes up the most space in the feed). Instagram doesn't make links in captions clickable, so put the GitHub URL in your **bio** (or a Linktree) and say "link in bio".

**Slide order:**
1. Hook: "Is my city getting hotter?" + 3 headline numbers
2. Warming stripes
3. Temperature trend lines (statistically significant)
4. Heatwave & cold-spell detection
5. Forecast to 2029
6. Dashboard screenshot
7. Tech stack + "link in bio"

### Caption 1: Main carousel (recommended)
```
Is my city actually getting hotter? 🌡️ I let the data decide.

I built a Climate Trend Analyzer in Python that crunches 35 years of daily climate data for Delhi, Mumbai, Chennai & Bengaluru 🇮🇳

📈 Warming: +0.18 to +0.32 °C every decade, in all 4 cities
🔥 Hot days per year: ~26 → ~50
🎯 My anomaly detector caught 98% of hidden heatwaves
🔮 Forecasts to 2029, tested against real hold-out years

The data is a realistic simulation (no access to government databases as a student 😅), which let me hide 140 extreme events and check whether my code could find them.

Swipe ➡️ to see the charts and dashboard.

Full code on GitHub 🔗 link in bio

#datascience #python #climatechange #climatedata #machinelearning #dataanalytics #coding #programming #studentlife #engineeringstudent #datavisualization #pythonprogramming #codinglife #techstudent #100daysofcode #india #portfolio #learnpython #datascientist #climateaction
```

### Caption 2: Short and punchy
```
35 years of climate data. 4 cities. 1 question: is it getting hotter? 🌡️🔥

Answer: yes. +0.18 to +0.32 °C per decade, statistically significant everywhere.

Built with Python, pandas, statsmodels, scikit-learn & Streamlit 🐍
Swipe for the charts ➡️ | Code: link in bio

#datascience #python #climatechange #machinelearning #codinglife #studentprojects
```

### Caption 3: Reel (screen recording of the dashboard + `03_pipeline_run.png`)
**On-screen text ideas:** "POV: you analyse 51,000 days of weather data" → "is it getting hotter?" → "yes. +0.32 °C/decade" → "link in bio".
```
From 51,000 messy weather records to a live climate dashboard 🌍➡️📊

Python did the heavy lifting: data cleaning, statistical trend tests, heatwave detection and forecasting.

Code in bio 🔗

#python #datascience #dashboard #streamlit #climatedata #codingreels #techreels #studentdeveloper
```

### Instagram bio line
```
🎓 Student | Data Science & Python
🌡️ Built: Climate Trend Analyzer
🔗 github.com/SNischayPrasad
```

---

## Posting checklist
- [ ] GitHub repo is public, README images load, and the repo is pinned on your profile
- [ ] Add your LinkedIn profile link to the Author section of `README.md`
- [ ] LinkedIn: post on a weekday morning (Tue–Thu, 8–10 AM IST works well); reply to every comment in the first hour
- [ ] Add the project to LinkedIn → *Profile → Add section → Projects* with the GitHub link
- [ ] Instagram: GitHub link in bio before posting; reshare the carousel to your Story with a "link" sticker
- [ ] Tag relevant people/pages only if they're genuinely connected (professor, college coding club)
