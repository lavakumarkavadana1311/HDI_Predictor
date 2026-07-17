🌐 **Live Demo:**
 [https://hdi-predictor-1-wyqk.onrender.com](https://hdi-predictor-1-wyqk.onrender.com)

*(Note: the free hosting tier sleeps after inactivity — the first load may take 10–30 seconds to wake up.)*

A Flask + Machine Learning web application that predicts a country's Human Development Index (HDI) — the UNDP's composite measure of life expectancy, education, and income — and classifies it into an official development tier. The system trains and compares Linear Regression and Random Forest models on real UNDP 2021 data, serves the best model through a REST API, and displays predictions through three dashboards: Home, Predict, and History.

---

## Project Structure

```
HDI_Predictor/
├── app.py
├── config.py
├── model_utils.py
├── db_utils.py
├── train_model.py
├── seed_history.py
├── requirements.txt
├── model.pkl
├── model_meta.json
├── country_data.json
├── dataset/
│   └── Human Development Index - Full.csv
├── static/
│   ├── css/style.css
│   ├── js/predict.js
│   ├── js/history.js
│   └── graphs/
│       ├── scatter_plot.png
│       ├── correlation_heatmap.png
│       ├── distribution_plot.png
│       └── strip_plot.png
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── predict.html
│   ├── history.html
│   └── 404.html
└── Project_Documentation/
    ├── 1. Brainstorming & Ideation/
    ├── 2. Requirement Analysis/
    ├── 3. Project Design Phase/
    ├── 4. Project Planning Phase/
    ├── 5. Project Development Phase/
    ├── 6.Project Testing/
    ├── 7.Project Documentation/
    └── 8.Project Demonstration/
```

---

## Dataset

`dataset/Human Development Index - Full.csv` — UNDP Human Development Report data for 195 countries. Key columns used:

| Column | Meaning |
|---|---|
| `Life Expectancy at Birth (2021)` | Years |
| `Expected Years of Schooling (2021)` | Years a child entering school today is expected to receive |
| `Mean Years of Schooling (2021)` | Average years of schooling completed by adults 25+ |
| `Gross National Income Per Capita (2021)` | USD, PPP-adjusted |
| `Human Development Index (2021)` | **Target**: 0–1 composite score |

GNI is log-transformed before training, mirroring the UNDP's own HDI formula (which uses ln(GNI) for its income sub-index) — this single change took the model's R² from ~0.90 to 0.999.

---

## Setup

Requires **Python 3.11**.

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## 1 — Train the Model

```bash
python train_model.py
```

Trains and compares Linear Regression vs Random Forest, keeps the higher-R² model, and exports `model.pkl`, `model_meta.json`, `country_data.json`, and the 4 EDA graphs in `static/graphs/`.

## 2 — Seed Demo History (optional)

```bash
python seed_history.py
```

Populates `predictions.db` with 32 realistic demo predictions so the History dashboard isn't empty on first run.

## 3 — Run the App

```bash
python app.py
```

Open **http://127.0.0.1:5000**.

---

## Deployment

Deployed on Render at the live demo link above, using:
- **Build Command**: `pip install -r requirements.txt && python train_model.py && python seed_history.py`
- **Start Command**: `gunicorn app:app`

Note: the free tier's filesystem is ephemeral, so `predictions.db` resets (and re-seeds) on every redeploy.

---

## Project Documentation

All formal project deliverables (brainstorming, requirements, design, planning, testing, documentation, and demonstration reports) are in [`Project_Documentation/`](./Project_Documentation), organized by phase.
