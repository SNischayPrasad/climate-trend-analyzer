"""
config.py
---------
Central configuration for the Climate Trend Analyzer.

Every path, city profile and analysis threshold lives here so that the rest of
the code never hard-codes a "magic number". Change a value here and the whole
pipeline picks it up.
"""

from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EXTERNAL_DIR = DATA_DIR / "external"          # real public datasets (NASA POWER etc.)

OUTPUT_DIR = ROOT_DIR / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"
TABLES_DIR = OUTPUT_DIR / "tables"
REPORTS_DIR = ROOT_DIR / "reports"
MODELS_DIR = ROOT_DIR / "models"

RAW_DATA_FILE = RAW_DIR / "climate_data_raw.csv"
INJECTED_EVENTS_FILE = RAW_DIR / "injected_events.csv"   # simulation ground truth
CLEAN_DATA_FILE = PROCESSED_DIR / "climate_data_clean.csv"
FEATURES_FILE = PROCESSED_DIR / "climate_features.csv"
MONTHLY_FILE = PROCESSED_DIR / "climate_monthly.csv"
YEARLY_FILE = PROCESSED_DIR / "climate_yearly.csv"

# --------------------------------------------------------------------------
# Simulation settings
# --------------------------------------------------------------------------
RANDOM_SEED = 42
START_DATE = "1990-01-01"
END_DATE = "2024-12-31"

# Each city has a realistic climate "personality".
#   temp_mean       : long-run average daily mean temperature (deg C)
#   temp_amplitude  : half the summer-winter swing (deg C)
#   peak_day        : day-of-year of the hottest period
#   warming_per_decade : long-term warming trend injected into the data
#   rain_annual_mm  : approximate annual rainfall total
#   monsoon_peak_day: day-of-year when rainfall peaks
#   monsoon_width   : how spread out (in days) the rainy season is
#   humidity_mean   : average relative humidity (%)
CITY_PROFILES = {
    "Delhi": dict(temp_mean=25.0, temp_amplitude=9.5, peak_day=150,
                  warming_per_decade=0.30, rain_annual_mm=790,
                  monsoon_peak_day=215, monsoon_width=30, humidity_mean=58),
    "Mumbai": dict(temp_mean=27.3, temp_amplitude=2.8, peak_day=135,
                   warming_per_decade=0.22, rain_annual_mm=2200,
                   monsoon_peak_day=200, monsoon_width=32, humidity_mean=74),
    "Chennai": dict(temp_mean=28.6, temp_amplitude=3.6, peak_day=150,
                    warming_per_decade=0.20, rain_annual_mm=1400,
                    monsoon_peak_day=315, monsoon_width=28, humidity_mean=71),
    "Bengaluru": dict(temp_mean=23.8, temp_amplitude=2.9, peak_day=105,
                      warming_per_decade=0.25, rain_annual_mm=970,
                      monsoon_peak_day=255, monsoon_width=45, humidity_mean=65),
}

# Data-quality problems we deliberately inject so the cleaning step has
# real work to do (just like real sensor data).
MISSING_RATE = 0.02          # 2% of values go missing
SENSOR_ERROR_RATE = 0.001    # 0.1% of values replaced by -999 / 999 sentinels
DUPLICATE_ROWS = 150         # duplicated records

# Extreme events injected into the simulation (ground truth for evaluation)
N_HEATWAVES_PER_CITY = 12
N_COLD_SPELLS_PER_CITY = 8
N_EXTREME_RAIN_PER_CITY = 15

# --------------------------------------------------------------------------
# Analysis settings
# --------------------------------------------------------------------------
BASELINE_START, BASELINE_END = 1991, 2020    # WMO-style 30-year climate normal
ZSCORE_THRESHOLD = 3.0                        # |z| above this = anomaly
RAIN_EXTREME_PERCENTILE = 99.5                # wet-day percentile = extreme rain
ISOLATION_CONTAMINATION = 0.02                # expected share of anomalous months
FORECAST_TEST_YEARS = 3                       # hold-out period for evaluation
FORECAST_HORIZON_MONTHS = 60                  # 5 years ahead
SIGNIFICANCE_LEVEL = 0.05

# Plot style
FIG_DPI = 150
CITY_COLORS = {
    "Delhi": "#d62728",
    "Mumbai": "#1f77b4",
    "Chennai": "#ff7f0e",
    "Bengaluru": "#2ca02c",
}


def rel(path) -> str:
    """Path relative to the project root (keeps logs short and machine-independent)."""
    return Path(path).resolve().relative_to(ROOT_DIR).as_posix()


def ensure_dirs() -> None:
    """Create every output folder if it does not exist yet."""
    for d in (RAW_DIR, PROCESSED_DIR, EXTERNAL_DIR, FIGURES_DIR,
              TABLES_DIR, REPORTS_DIR, MODELS_DIR):
        d.mkdir(parents=True, exist_ok=True)
