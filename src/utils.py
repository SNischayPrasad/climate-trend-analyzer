"""
utils.py
--------
Small helpers shared by every module: logging, figure saving, and timing.
"""

import logging
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import matplotlib

matplotlib.use("Agg")            # render to files; no GUI window needed
import matplotlib.pyplot as plt  # noqa: E402

from src import config  # noqa: E402


def get_logger(name: str) -> logging.Logger:
    """Return a logger that prints 'time | LEVEL | module | message'."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Windows terminals default to cp1252, which cannot print "°C"
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)-22s | %(message)s", "%H:%M:%S"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def save_figure(fig, filename: str) -> Path:
    """Save a matplotlib figure into outputs/figures and close it."""
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = config.FIGURES_DIR / filename
    fig.savefig(path, dpi=config.FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    return path


def set_plot_style() -> None:
    """One consistent, clean look for every chart in the project."""
    import seaborn as sns
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update({
        "figure.figsize": (12, 6),
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
    })


def save_table(df, filename: str, index: bool = False) -> Path:
    """Save a DataFrame into outputs/tables as CSV."""
    config.TABLES_DIR.mkdir(parents=True, exist_ok=True)
    path = config.TABLES_DIR / filename
    df.to_csv(path, index=index)
    return path


@contextmanager
def timed(step_name: str, logger: logging.Logger):
    """Context manager that logs how long a pipeline step took."""
    start = time.perf_counter()
    logger.info("=" * 60)
    logger.info("STEP: %s", step_name)
    yield
    logger.info("DONE: %s (%.1fs)", step_name, time.perf_counter() - start)
