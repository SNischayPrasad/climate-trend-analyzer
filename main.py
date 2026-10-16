"""
main.py - Climate Trend Analyzer pipeline entry point
=====================================================

Run everything:
    python main.py

Run one step at a time:
    python main.py --step generate     # 1. simulate raw climate data
    python main.py --step clean        # 2. clean + feature engineering
    python main.py --step eda          # 3. exploratory charts
    python main.py --step trend        # 4. trend tests + charts
    python main.py --step anomaly      # 5. anomaly detection
    python main.py --step forecast     # 6. forecasting
    python main.py --step report       # 7. insights report

Use a real public dataset instead of the simulation:
    python main.py --source external --input data/external/nasa_power_india.csv
"""

import argparse
import sys

import pandas as pd

from src import config
from src.utils import get_logger, timed

logger = get_logger("pipeline")
STEPS = ["generate", "clean", "eda", "trend", "anomaly", "forecast", "report"]


def _load_features():
    if not config.FEATURES_FILE.exists():
        sys.exit("Processed data not found. Run: python main.py --step clean")
    df = pd.read_csv(config.FEATURES_FILE, parse_dates=["date"])
    monthly = pd.read_csv(config.MONTHLY_FILE, parse_dates=["date"])
    yearly = pd.read_csv(config.YEARLY_FILE)
    return df, monthly, yearly


def run(step: str, source: str, input_path: str | None) -> None:
    config.ensure_dirs()
    run_all = step == "all"

    if (run_all or step == "generate") and source == "simulated":
        from src.data_generator import generate_climate_data
        with timed("1/7 Generate simulated climate data", logger):
            generate_climate_data()

    if run_all or step == "clean":
        from src.data_loader import load_raw_data
        from src.feature_engineering import run_feature_engineering
        from src.preprocessing import clean_data
        with timed("2/7 Clean data + feature engineering", logger):
            raw = load_raw_data(input_path or config.RAW_DATA_FILE)
            run_feature_engineering(clean_data(raw))

    if run_all or step in STEPS[2:]:
        df, monthly, yearly = _load_features()

    if run_all or step == "eda":
        from src.eda import run_eda
        with timed("3/7 Exploratory data analysis", logger):
            run_eda(df)

    if run_all or step == "trend":
        from src.trend_analysis import run_trend_analysis
        with timed("4/7 Climate trend analysis", logger):
            run_trend_analysis(df, monthly, yearly)

    if run_all or step == "anomaly":
        from src.anomaly_detection import run_anomaly_detection
        with timed("5/7 Anomaly detection", logger):
            run_anomaly_detection(df, monthly)

    if run_all or step == "forecast":
        from src.forecasting import run_forecasting
        with timed("6/7 Forecasting", logger):
            run_forecasting(monthly)

    if run_all or step == "report":
        from src.report_generator import generate_report
        with timed("7/7 Insights report", logger):
            generate_report()

    if run_all:
        logger.info("=" * 60)
        logger.info("PIPELINE COMPLETE")
        logger.info("  Figures : %s", config.rel(config.FIGURES_DIR))
        logger.info("  Tables  : %s", config.rel(config.TABLES_DIR))
        logger.info("  Report  : %s", config.rel(config.REPORTS_DIR / "climate_insights_report.md"))
        logger.info("  Dashboard: streamlit run app/streamlit_app.py")


def main():
    parser = argparse.ArgumentParser(description="Climate Trend Analyzer pipeline")
    parser.add_argument("--step", choices=["all"] + STEPS, default="all")
    parser.add_argument("--source", choices=["simulated", "external"], default="simulated",
                        help="'simulated' generates data; 'external' uses --input CSV")
    parser.add_argument("--input", default=None, help="Path to an external CSV in the standard schema")
    args = parser.parse_args()
    if args.source == "external" and not args.input:
        parser.error("--source external requires --input <csv path>")
    run(args.step, args.source, args.input)


if __name__ == "__main__":
    main()
