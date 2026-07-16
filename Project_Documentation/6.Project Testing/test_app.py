"""
Lightweight smoke tests for the HDI Predictor app.

Run with:  python test_app.py
(from inside "Project_Documentation/6.Project Testing", after training the
model at the repo root with train_model.py)
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from model_utils import predict_hdi, classify_tier  # noqa: E402


def test_tier_bands():
    assert classify_tier(0.95) == "Very High"
    assert classify_tier(0.75) == "High"
    assert classify_tier(0.60) == "Medium"
    assert classify_tier(0.30) == "Low"
    print("PASS: classify_tier boundary cases")


def test_predict_very_high():
    result = predict_hdi(82.0, 17.0, 13.0, 55000)
    assert 0.0 <= result["hdi"] <= 1.0
    assert result["tier"] in ("Very High", "High")
    print(f"PASS: high-indicator scenario -> HDI={result['hdi']}, tier={result['tier']}")


def test_predict_low():
    result = predict_hdi(52.0, 6.0, 3.0, 1200)
    assert 0.0 <= result["hdi"] <= 1.0
    assert result["tier"] in ("Low", "Medium")
    print(f"PASS: low-indicator scenario -> HDI={result['hdi']}, tier={result['tier']}")


def test_predict_output_clamped():
    # Absurdly high inputs should still clamp to a valid [0, 1] HDI
    result = predict_hdi(99.0, 25.0, 20.0, 200000)
    assert 0.0 <= result["hdi"] <= 1.0
    print(f"PASS: extreme inputs clamp correctly -> HDI={result['hdi']}")


if __name__ == "__main__":
    test_tier_bands()
    test_predict_very_high()
    test_predict_low()
    test_predict_output_clamped()
    print("\nAll tests passed.")
