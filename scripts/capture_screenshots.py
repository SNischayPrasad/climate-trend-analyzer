"""
capture_screenshots.py
----------------------
Automatically captures proof screenshots of the Streamlit dashboard and
builds a demo GIF for the README.

Run AFTER `python main.py`:
    pip install playwright
    python scripts/capture_screenshots.py

Uses Microsoft Edge (pre-installed on Windows) or Google Chrome, so no extra
browser download is needed. Outputs go to images/screenshots/ and images/demo.gif.
"""

import subprocess
import sys
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "images" / "screenshots"
PORT = 8502
URL = f"http://localhost:{PORT}"

TABS = [  # (tab label text, file name)
    ("Trends", "05_dashboard_trends.png"),
    ("Anomalies", "06_dashboard_anomalies.png"),
    ("Forecast", "07_dashboard_forecast.png"),
    ("Insights", "08_dashboard_insights.png"),
    ("Seasonality", "12_dashboard_seasonality.png"),
]


def start_dashboard() -> subprocess.Popen:
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app/streamlit_app.py",
         "--server.headless", "true", "--server.port", str(PORT)],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(6)
    return proc


def launch_browser(p):
    for channel in ("msedge", "chrome", None):
        try:
            return p.chromium.launch(channel=channel) if channel else p.chromium.launch()
        except Exception:
            continue
    raise RuntimeError("No browser found. Run: python -m playwright install chromium")


def wait_for_charts(page):
    page.wait_for_timeout(1500)
    try:
        page.wait_for_selector(".js-plotly-plot", timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(2500)


def main():
    SHOTS.mkdir(parents=True, exist_ok=True)
    proc = start_dashboard()
    frames = []
    try:
        with sync_playwright() as p:
            browser = launch_browser(p)
            page = browser.new_page(viewport={"width": 1440, "height": 1100},
                                    color_scheme="light", device_scale_factor=1)
            page.goto(URL, wait_until="networkidle")
            page.wait_for_selector("text=Climate Trend Analyzer", timeout=60000)
            wait_for_charts(page)

            for label, filename in TABS:
                page.get_by_role("tab", name=label).click()
                wait_for_charts(page)
                path = SHOTS / filename
                page.screenshot(path=str(path))
                frames.append(Image.open(path).convert("RGB"))
                print("saved", path.relative_to(ROOT))

            # Bonus: a second city to show the selector works
            page.get_by_role("tab", name="Trends").click()
            page.locator("[data-testid='stSelectbox']").first.click()
            page.get_by_role("option", name="Mumbai").click()
            wait_for_charts(page)
            path = SHOTS / "13_dashboard_mumbai.png"
            page.screenshot(path=str(path))
            frames.append(Image.open(path).convert("RGB"))
            print("saved", path.relative_to(ROOT))
            browser.close()
    finally:
        proc.terminate()

    # Demo GIF (resized to keep the file small)
    small = [f.resize((960, int(960 * f.height / f.width))) for f in frames]
    gif = ROOT / "images" / "demo.gif"
    small[0].save(gif, save_all=True, append_images=small[1:], duration=2200, loop=0, optimize=True)
    print("saved", gif.relative_to(ROOT), f"({gif.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
