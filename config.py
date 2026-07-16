"""
Central configuration for the HDI Predictor application.
Keeping these values in one place makes the app easier to scale,
test, and deploy (e.g. swapping SQLite for Postgres later only
means changing DB_PATH / db_utils.py).
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Paths -----------------------------------------------------------------
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
MODEL_META_PATH = os.path.join(BASE_DIR, "model_meta.json")
COUNTRY_DATA_PATH = os.path.join(BASE_DIR, "country_data.json")
DB_PATH = os.path.join(BASE_DIR, "predictions.db")
GRAPHS_DIR = os.path.join(BASE_DIR, "static", "graphs")

# --- Model / feature configuration -----------------------------------------
FEATURE_LABELS = {
    "life_exp": "Life Expectancy at Birth (years)",
    "expected_schooling": "Expected Years of Schooling",
    "mean_schooling": "Mean Years of Schooling",
    "gni": "Gross National Income Per Capita (USD, PPP)",
}
FEATURE_ORDER = ["life_exp", "expected_schooling", "mean_schooling", "gni"]

# --- HDI tier thresholds (official UNDP classification bands) --------------
TIER_BANDS = [
    ("Very High", 0.800, 1.001),
    ("High", 0.700, 0.800),
    ("Medium", 0.550, 0.700),
    ("Low", 0.000, 0.550),
]

TIER_COLORS = {
    "Very High": "#2E7D6B",
    "High": "#3E7CB1",
    "Medium": "#C9A227",
    "Low": "#C1543D",
}

# --- History dashboard -------------------------------------------------------
HISTORY_DISPLAY_LIMIT = 50   # show at most this many rows on the History page
SEED_HISTORY_COUNT = 32      # how many demo records to seed on first run
