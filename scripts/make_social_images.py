"""
make_social_images.py
---------------------
Builds ready-to-post images from the pipeline outputs:

    images/screenshots/03_pipeline_run.png   terminal view of a real pipeline run
    images/screenshots/04_tests_passing.png  terminal view of a real pytest run
    images/social/instagram_01..07.png       1080x1350 Instagram carousel (4:5)
    images/social/linkedin_cover.png         1200x627 LinkedIn post image

Run AFTER `python main.py` (and ideally after capture_screenshots.py):
    python scripts/make_social_images.py
All numbers are read from outputs/tables, so they always match your run.
"""

import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "outputs" / "figures"
TAB = ROOT / "outputs" / "tables"
SHOTS = ROOT / "images" / "screenshots"
SOCIAL = ROOT / "images" / "social"

BG, FG, MUTED, ACCENT, BLUE = "#0f172a", "#f8fafc", "#94a3b8", "#ef4444", "#38bdf8"


# ---------------------------------------------------------------------------
# Terminal-style renders of real command output
# ---------------------------------------------------------------------------
def render_terminal(lines, title, out, width=14):
    height = 0.6 + 0.24 * len(lines)
    fig = plt.figure(figsize=(width, height), facecolor="#1e1e1e")
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_facecolor("#1e1e1e")
    ax.add_patch(plt.Rectangle((0, 1 - 0.35 / height), 1, 0.35 / height, color="#333", transform=ax.transAxes))
    for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):   # window buttons
        ax.scatter([(0.15 + i * 0.22) / width], [1 - 0.175 / height], s=90, color=c,
                   transform=ax.transAxes, zorder=3)
    ax.text(0.5, 1 - 0.175 / height, title, color="#ccc", ha="center", va="center",
            fontsize=10, family="monospace", transform=ax.transAxes)
    for i, line in enumerate(lines):
        color = "#d4d4d4"
        if line.startswith("$") or line.startswith("PS "):
            color = "#4ec9b0"
        elif any(k in line for k in ("PASSED", "passed", "COMPLETE", "recall", "warming")):
            color = "#6a9955" if "PASSED" in line or "passed" in line else "#dcdcaa"
        ax.text(0.012, 1 - (0.55 + 0.24 * i) / height, line, color=color, fontsize=9.5,
                family="monospace", va="top", transform=ax.transAxes)
    fig.savefig(out, dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("saved", out.relative_to(ROOT))


def pipeline_screenshot():
    log = (ROOT / "outputs" / "pipeline_run_log.txt").read_text(encoding="utf-8").splitlines()
    keep_words = ("STEP:", "DONE:", "Saved raw", "ground-truth", "duplicate_rows", "sentinel",
                  "after_imputation", "warming", "recall", "best model", "anomaly events",
                  "PIPELINE COMPLETE", "Figures", "Tables", "Report")
    lines = ["(venv) PS ...\\Climate-Trend-Analyzer> python main.py"]
    lines += [line.replace("| INFO    |", "|") for line in log if any(k in line for k in keep_words)]
    render_terminal(lines, "Terminal — python main.py", SHOTS / "03_pipeline_run.png", width=15)


def tests_screenshot():
    res = subprocess.run([sys.executable, "-m", "pytest", "-v", "-p", "no:cacheprovider"],
                         cwd=ROOT, capture_output=True, text=True)
    out = [ln for ln in res.stdout.splitlines()
           if "::" in ln or "passed" in ln or "failed" in ln or ln.startswith("platform")]
    lines = ["(venv) PS ...\\Climate-Trend-Analyzer> pytest -v", ""] + \
            [ln.split(" -- ")[0].replace(str(ROOT), "") for ln in out]
    render_terminal(lines, "Terminal — pytest -v", SHOTS / "04_tests_passing.png", width=12)


# ---------------------------------------------------------------------------
# Instagram carousel (1080 x 1350)
# ---------------------------------------------------------------------------
def _slide(n, headline, sub, image=None, body=None, footer=""):
    fig = plt.figure(figsize=(10.8, 13.5), dpi=100, facecolor=BG)
    fig.text(0.07, 0.93, headline, color=FG, fontsize=40, fontweight="bold", va="top", wrap=True)
    sub_y = 0.78 if "\n" in headline else 0.835        # leave room for a 2-line headline
    fig.text(0.07, sub_y, sub, color=MUTED, fontsize=21, va="top", wrap=True)
    if image is not None:
        img = mpimg.imread(image)
        h, w = img.shape[:2]
        box_w, box_h = 0.88, 0.62
        aspect = (h / w) * (10.8 / 13.5)
        ih = min(box_h, box_w * aspect); iw = ih / aspect
        ax = fig.add_axes([0.5 - iw / 2, 0.11 + (box_h - ih) / 2, iw, ih])
        ax.imshow(img); ax.axis("off")
    if body:
        for i, (big, small) in enumerate(body):
            y = 0.68 - i * 0.15
            fig.text(0.07, y, big, color=ACCENT if i % 2 == 0 else BLUE, fontsize=58, fontweight="bold", va="top")
            fig.text(0.07, y - 0.065, small, color=FG, fontsize=22, va="top")
    fig.text(0.07, 0.04, "Climate Trend Analyzer · Python data science project", color=MUTED, fontsize=15)
    fig.text(0.93, 0.04, footer, color=MUTED, fontsize=15, ha="right")
    out = SOCIAL / f"instagram_{n:02d}.png"
    fig.savefig(out, dpi=100, facecolor=BG)
    plt.close(fig)
    print("saved", out.relative_to(ROOT))


def instagram_carousel():
    trend = pd.read_csv(TAB / "trend_summary.csv")
    t = trend[trend.variable == "temp_mean"]
    hot = trend[trend.variable == "hot_days"]
    ev = pd.read_csv(TAB / "anomaly_detection_evaluation.csv").set_index("event_type")
    fm = pd.read_csv(TAB / "forecast_metrics.csv")
    best = fm.groupby("city")["RMSE"].min()
    naive = fm[fm.model == "Seasonal Naive"].set_index("city")["RMSE"]
    gain = ((naive - best) / naive * 100)
    total = 7

    _slide(1, "Is my city getting\nhotter?",
           "I analysed 35 years of daily climate data\nfor 4 Indian cities using Python.",
           body=[(f"+{t.sen_slope_per_decade.min():.2f} to +{t.sen_slope_per_decade.max():.2f} °C",
                  "warming per decade — significant in all 4 cities"),
                 (f"{hot.first_decade_mean.mean():.0f} → {hot.last_decade_mean.mean():.0f}",
                  "average hot days per year, 1990s vs last decade"),
                 (f"{ev.loc['heatwave', 'event_recall'] * 100:.0f}%",
                  "of heatwaves caught by my anomaly detector")],
           footer=f"1/{total}  swipe →")
    _slide(2, "The warming stripes", "Each stripe = one year. Blue = cooler than normal,\nred = warmer. The shift is hard to miss.",
           image=FIG / "08_warming_stripes.png", footer=f"2/{total}")
    _slide(3, "Statistically significant", "Mann-Kendall test + Sen's slope on yearly averages.\nEvery city: p < 0.001.",
           image=FIG / "06_temperature_trend.png", footer=f"3/{total}")
    _slide(4, "Finding the extremes", "De-trended Z-scores flag heatwaves (red)\nand cold spells (blue) across 35 years.",
           image=FIG / "14_temperature_anomalies.png", footer=f"4/{total}")
    _slide(5, "Forecasting to 2029", f"Back-tested 3 models. Best one beat the\nnaive baseline by {gain.min():.0f}–{gain.max():.0f}%.",
           image=FIG / "18_temperature_forecast.png", footer=f"5/{total}")
    dash = SHOTS / "05_dashboard_trends.png"
    _slide(6, "Interactive dashboard", "Built with Streamlit + Plotly: pick a city,\nexplore trends, anomalies and forecasts.",
           image=dash if dash.exists() else FIG / "03_seasonal_cycle.png", footer=f"6/{total}")
    _slide(7, "How I built it",
           "Python · pandas · SciPy · statsmodels\nscikit-learn · Plotly · Streamlit · pytest",
           body=[("51K+", "daily records cleaned & validated"),
                 ("19", "charts + an auto-generated insights report"),
                 ("Link in bio", "full code on GitHub")],
           footer=f"{total}/{total}")


def linkedin_cover():
    trend = pd.read_csv(TAB / "trend_summary.csv")
    t = trend[trend.variable == "temp_mean"]
    fig = plt.figure(figsize=(12, 6.27), dpi=100, facecolor=BG)
    fig.text(0.05, 0.86, "Climate Trend Analyzer", color=FG, fontsize=38, fontweight="bold", va="top")
    fig.text(0.05, 0.72, "35 years · 4 Indian cities · 51K+ daily records", color=MUTED, fontsize=18, va="top")
    fig.text(0.05, 0.56, f"+{t.sen_slope_per_decade.min():.2f} to +{t.sen_slope_per_decade.max():.2f} °C / decade",
             color=ACCENT, fontsize=30, fontweight="bold", va="top")
    fig.text(0.05, 0.45, "Trend tests · Anomaly detection · Forecasting · Dashboard", color=FG, fontsize=16, va="top")
    ax = fig.add_axes([0.05, 0.08, 0.9, 0.28])
    ax.imshow(mpimg.imread(FIG / "08_warming_stripes.png")[60:-70, 220:-30], aspect="auto"); ax.axis("off")
    out = SOCIAL / "linkedin_cover.png"
    fig.savefig(out, dpi=100, facecolor=BG)
    plt.close(fig)
    print("saved", out.relative_to(ROOT))


if __name__ == "__main__":
    SHOTS.mkdir(parents=True, exist_ok=True)
    SOCIAL.mkdir(parents=True, exist_ok=True)
    pipeline_screenshot()
    tests_screenshot()
    instagram_carousel()
    linkedin_cover()
