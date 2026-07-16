"""
HDI Predictor -- Model Training Script
=======================================

Loads the UNDP Human Development Index dataset, engineers features,
trains and compares two regression models (Linear Regression and
Random Forest), and persists:

  - model.pkl           the best-performing trained model
  - model_meta.json      metadata (features, scores, timestamp)
  - country_data.json    a compact per-country dataset used by the
                          web app (home page stats + "load a country"
                          helper on the Predict page)
  - graphs/*.png         exploratory data analysis visuals

Run with:  python train_model.py
"""

import os
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error

from config import (
    MODEL_PATH, MODEL_META_PATH, COUNTRY_DATA_PATH, GRAPHS_DIR,
    FEATURE_ORDER, TIER_BANDS,
)

DATASET_PATH = os.path.join("dataset", "Human Development Index - Full.csv")

# Atlas-inspired palette to keep generated graphs visually consistent
# with the web app's theme.
INK = "#1C2530"
GOLD = "#C9A227"
TEAL = "#2E7D6B"
CORAL = "#C1543D"
NAVY = "#16324F"


def classify_tier(hdi):
    for name, low, high in TIER_BANDS:
        if low <= hdi < high:
            return name
    return "Low"


def main():
    print("=" * 60)
    print("HDI PREDICTOR -- MODEL TRAINING")
    print("=" * 60)

    # ------------------------------------------------------------------
    # 1. Load & select columns
    # ------------------------------------------------------------------
    df = pd.read_csv(DATASET_PATH)
    print(f"\nDataset loaded: {df.shape[0]} countries, {df.shape[1]} columns")

    cols = {
        "Country": "country",
        "ISO3": "iso3",
        "Human Development Groups": "group",
        "Life Expectancy at Birth (2021)": "life_exp",
        "Expected Years of Schooling (2021)": "expected_schooling",
        "Mean Years of Schooling (2021)": "mean_schooling",
        "Gross National Income Per Capita (2021)": "gni",
        "Human Development Index (2021)": "hdi",
    }
    data = df[list(cols.keys())].rename(columns=cols)

    # Drop rows with no target -- can't train or report on these
    data = data.dropna(subset=["hdi"])

    # Fill any remaining missing feature values with column means
    feature_cols = ["life_exp", "expected_schooling", "mean_schooling", "gni"]
    data[feature_cols] = data[feature_cols].fillna(data[feature_cols].mean())

    print(f"Usable rows after cleaning: {len(data)}")

    # ------------------------------------------------------------------
    # 2. Feature engineering
    # ------------------------------------------------------------------
    # The real HDI formula uses ln(GNI) for the income sub-index, so a
    # log transform brings this feature much closer to a linear
    # relationship with the target -- a simple change that meaningfully
    # boosts accuracy over using raw GNI.
    data["log_gni"] = np.log(data["gni"].clip(lower=1))

    X = data[["life_exp", "expected_schooling", "mean_schooling", "log_gni"]]
    y = data["hdi"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"Train/test split: {len(X_train)} / {len(X_test)}")

    # ------------------------------------------------------------------
    # 3. Train & compare candidate models
    # ------------------------------------------------------------------
    candidates = {
        "LinearRegression": LinearRegression(),
        "RandomForestRegressor": RandomForestRegressor(
            n_estimators=300, max_depth=8, random_state=42
        ),
    }

    results = {}
    for name, model in candidates.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        r2 = r2_score(y_test, preds)
        mae = mean_absolute_error(y_test, preds)
        results[name] = {"model": model, "r2": r2, "mae": mae}
        print(f"\n{name}")
        print(f"  R^2 : {r2:.4f}")
        print(f"  MAE : {mae:.4f}")

    best_name = max(results, key=lambda k: results[k]["r2"])
    best = results[best_name]
    print(f"\nBest model: {best_name} (R^2 = {best['r2']:.4f})")

    # ------------------------------------------------------------------
    # 4. Persist model + metadata
    # ------------------------------------------------------------------
    joblib.dump(best["model"], MODEL_PATH)

    meta = {
        "model_type": best_name,
        "features": ["life_exp", "expected_schooling", "mean_schooling", "log_gni"],
        "feature_display": FEATURE_ORDER,
        "r2_score": round(best["r2"], 4),
        "mae": round(best["mae"], 4),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "candidates": {k: {"r2": round(v["r2"], 4), "mae": round(v["mae"], 4)}
                        for k, v in results.items()},
    }
    with open(MODEL_META_PATH, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"\nSaved model -> {MODEL_PATH}")
    print(f"Saved metadata -> {MODEL_META_PATH}")

    # ------------------------------------------------------------------
    # 5. Export compact per-country dataset for the web app
    # ------------------------------------------------------------------
    data["tier"] = data["hdi"].apply(classify_tier)
    export_cols = ["country", "iso3", "group", "tier", "life_exp",
                   "expected_schooling", "mean_schooling", "gni", "hdi"]
    country_records = data[export_cols].sort_values("hdi", ascending=False).to_dict(
        orient="records"
    )
    with open(COUNTRY_DATA_PATH, "w") as f:
        json.dump(country_records, f, indent=2)
    print(f"Saved country dataset -> {COUNTRY_DATA_PATH} ({len(country_records)} countries)")

    # ------------------------------------------------------------------
    # 6. Exploratory graphs (themed to match the app)
    # ------------------------------------------------------------------
    os.makedirs(GRAPHS_DIR, exist_ok=True)
    sns.set_theme(style="whitegrid", rc={
        "axes.facecolor": "#FCFAF3",
        "figure.facecolor": "#FCFAF3",
        "grid.color": "#E3DCC9",
    })

    # Scatter: life expectancy vs HDI, colored by tier
    plt.figure(figsize=(8, 6))
    tier_colors = {"Very High": TEAL, "High": NAVY, "Medium": GOLD, "Low": CORAL}
    for tier, color in tier_colors.items():
        subset = data[data["tier"] == tier]
        plt.scatter(subset["life_exp"], subset["hdi"], label=tier,
                    color=color, alpha=0.75, edgecolor="white", linewidth=0.5)
    plt.title("Life Expectancy vs HDI", fontsize=14, color=INK, weight="bold")
    plt.xlabel("Life Expectancy at Birth (years)")
    plt.ylabel("Human Development Index")
    plt.legend(title="Tier")
    plt.tight_layout()
    plt.savefig(os.path.join(GRAPHS_DIR, "scatter_plot.png"), dpi=140)
    plt.close()

    # Correlation heatmap
    plt.figure(figsize=(7, 6))
    corr = data[["life_exp", "expected_schooling", "mean_schooling", "gni", "hdi"]].corr()
    sns.heatmap(corr, annot=True, cmap="YlGnBu", fmt=".2f", linewidths=0.5,
                cbar_kws={"label": "Correlation"})
    plt.title("Correlation Heatmap", fontsize=14, color=INK, weight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(GRAPHS_DIR, "correlation_heatmap.png"), dpi=140)
    plt.close()

    # Distribution plot
    plt.figure(figsize=(8, 6))
    sns.histplot(data["hdi"], kde=True, color=TEAL)
    plt.title("Distribution of HDI Scores", fontsize=14, color=INK, weight="bold")
    plt.xlabel("HDI Score")
    plt.ylabel("Number of Countries")
    plt.tight_layout()
    plt.savefig(os.path.join(GRAPHS_DIR, "distribution_plot.png"), dpi=140)
    plt.close()

    # Strip plot by tier
    plt.figure(figsize=(9, 6))
    order = ["Low", "Medium", "High", "Very High"]
    sns.stripplot(data=data, x="tier", y="hdi", order=order, hue="tier",
                  palette=tier_colors, size=6, alpha=0.8, legend=False)
    plt.title("HDI Scores by Development Tier", fontsize=14, color=INK, weight="bold")
    plt.xlabel("Development Tier")
    plt.ylabel("HDI Score")
    plt.tight_layout()
    plt.savefig(os.path.join(GRAPHS_DIR, "strip_plot.png"), dpi=140)
    plt.close()

    print(f"Saved 4 graphs -> {GRAPHS_DIR}/")
    print("\nTraining complete.")


if __name__ == "__main__":
    main()
