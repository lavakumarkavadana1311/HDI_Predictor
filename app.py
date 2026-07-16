"""
Human Development Index (HDI) Predictor -- Flask Web Application
==================================================================

Three dashboards:
  /          Home      -- project overview + global HDI insights
  /predict   Predict   -- ML-powered HDI prediction form
  /history   History   -- last 50 predictions with trends

Plus a small JSON API (/api/...) used by the front-end JavaScript so
pages update instantly without full reloads.
"""

import json
from datetime import datetime, timezone

from flask import Flask, render_template, request, jsonify

from config import (
    COUNTRY_DATA_PATH, FEATURE_LABELS, TIER_COLORS, HISTORY_DISPLAY_LIMIT,
)
from model_utils import predict_hdi, get_meta
from db_utils import (
    init_db, insert_prediction, get_history, get_history_count,
    delete_prediction, clear_history,
)

app = Flask(__name__)

with open(COUNTRY_DATA_PATH, "r") as f:
    COUNTRY_DATA = json.load(f)

init_db()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def compute_global_stats():
    """Aggregate stats for the Home dashboard."""
    hdis = [c["hdi"] for c in COUNTRY_DATA]
    tier_counts = {"Very High": 0, "High": 0, "Medium": 0, "Low": 0}
    for c in COUNTRY_DATA:
        tier_counts[c["tier"]] = tier_counts.get(c["tier"], 0) + 1

    ranked = sorted(COUNTRY_DATA, key=lambda c: c["hdi"], reverse=True)
    return {
        "country_count": len(COUNTRY_DATA),
        "avg_hdi": round(sum(hdis) / len(hdis), 3),
        "max_hdi": round(max(hdis), 3),
        "min_hdi": round(min(hdis), 3),
        "tier_counts": tier_counts,
        "top5": ranked[:5],
        "bottom5": ranked[-5:][::-1],
    }


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    stats = compute_global_stats()
    meta = get_meta()
    return render_template(
        "home.html",
        stats=stats,
        tier_colors=TIER_COLORS,
        meta=meta,
        active_page="home",
    )


@app.route("/predict")
def predict_page():
    return render_template(
        "predict.html",
        feature_labels=FEATURE_LABELS,
        tier_colors=TIER_COLORS,
        countries=COUNTRY_DATA,
        meta=get_meta(),
        active_page="predict",
    )


@app.route("/history")
def history_page():
    rows = get_history(HISTORY_DISPLAY_LIMIT)
    total_count = get_history_count()
    return render_template(
        "history.html",
        rows=rows,
        total_count=total_count,
        display_limit=HISTORY_DISPLAY_LIMIT,
        tier_colors=TIER_COLORS,
        active_page="history",
    )


# ---------------------------------------------------------------------------
# JSON API
# ---------------------------------------------------------------------------
@app.route("/api/predict", methods=["POST"])
def api_predict():
    payload = request.get_json(silent=True) or request.form

    try:
        life_exp = float(payload.get("life_exp"))
        expected_schooling = float(payload.get("expected_schooling"))
        mean_schooling = float(payload.get("mean_schooling"))
        gni = float(payload.get("gni"))
        label = (payload.get("label") or "").strip() or None
    except (TypeError, ValueError):
        return jsonify({"error": "Please enter valid numeric values for every field."}), 400

    errors = []
    if life_exp <= 0 or life_exp > 100:
        errors.append("Life expectancy must be between 0 and 100 years.")
    if expected_schooling < 0 or expected_schooling > 25:
        errors.append("Expected years of schooling must be between 0 and 25.")
    if mean_schooling < 0 or mean_schooling > 20:
        errors.append("Mean years of schooling must be between 0 and 20.")
    if gni <= 0:
        errors.append("Gross National Income must be greater than 0.")
    if expected_schooling < mean_schooling:
        errors.append("Expected schooling is usually greater than or equal to mean schooling.")

    if errors:
        return jsonify({"error": " ".join(errors)}), 400

    result = predict_hdi(life_exp, expected_schooling, mean_schooling, gni)
    created_at = datetime.now(timezone.utc).isoformat()

    record_id = insert_prediction(
        label=label,
        life_exp=life_exp,
        expected_schooling=expected_schooling,
        mean_schooling=mean_schooling,
        gni=gni,
        predicted_hdi=result["hdi"],
        predicted_tier=result["tier"],
        created_at=created_at,
    )

    return jsonify({
        "id": record_id,
        "hdi": result["hdi"],
        "tier": result["tier"],
        "tier_color": TIER_COLORS.get(result["tier"], "#333"),
        "created_at": created_at,
        "inputs": {
            "life_exp": life_exp,
            "expected_schooling": expected_schooling,
            "mean_schooling": mean_schooling,
            "gni": gni,
            "label": label,
        },
    })


@app.route("/api/history")
def api_history():
    limit = request.args.get("limit", HISTORY_DISPLAY_LIMIT, type=int)
    return jsonify(get_history(limit))


@app.route("/api/history/<int:record_id>", methods=["DELETE"])
def api_delete_history(record_id):
    delete_prediction(record_id)
    return jsonify({"status": "deleted", "id": record_id})


@app.route("/api/history/clear", methods=["POST"])
def api_clear_history():
    clear_history()
    return jsonify({"status": "cleared"})


@app.errorhandler(404)
def not_found(_e):
    return render_template("404.html", active_page=""), 404


if __name__ == "__main__":
    app.run(debug=True)
