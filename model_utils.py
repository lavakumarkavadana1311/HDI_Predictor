"""
Everything related to the ML model lives here: loading the trained
pipeline, running predictions, and turning a raw HDI score into a
human-readable development tier.
"""

import json
import math
import joblib
import pandas as pd

from config import MODEL_PATH, MODEL_META_PATH, FEATURE_ORDER, TIER_BANDS

_model = None
_meta = None


def get_model():
    """Lazily load and cache the trained model (avoids reloading per request)."""
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model


def get_meta():
    """Lazily load and cache model metadata (R2, MAE, training date, etc.)."""
    global _meta
    if _meta is None:
        with open(MODEL_META_PATH, "r") as f:
            _meta = json.load(f)
    return _meta


def classify_tier(hdi_score):
    """Map a numeric HDI score to its official UNDP development tier."""
    for tier_name, low, high in TIER_BANDS:
        if low <= hdi_score < high:
            return tier_name
    return "Low"


def predict_hdi(life_exp, expected_schooling, mean_schooling, gni):
    """
    Run the trained model on raw human-friendly inputs and return a dict
    with the predicted HDI score (clamped to [0, 1]) and its tier.

    GNI is log-transformed internally to mirror the real HDI formula,
    which uses ln(GNI) for the income sub-index -- this keeps the
    feature relationship close to linear and meaningfully improves
    model accuracy over using raw GNI.
    """
    model = get_model()

    log_gni = math.log(max(gni, 1))
    features = pd.DataFrame(
        [[life_exp, expected_schooling, mean_schooling, log_gni]],
        columns=["life_exp", "expected_schooling", "mean_schooling", "log_gni"],
    )

    raw_prediction = float(model.predict(features)[0])
    prediction = max(0.0, min(raw_prediction, 1.0))

    return {
        "hdi": round(prediction, 3),
        "tier": classify_tier(prediction),
    }
