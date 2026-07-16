"""
Seeds the predictions database with realistic demo history so the
History dashboard isn't empty on first run. Picks a spread of real
countries across all four tiers and runs them through the trained
model, backdating timestamps over the last few weeks.

Run once with:  python seed_history.py
(safe to re-run -- it clears existing rows first)
"""

import json
import random
from datetime import datetime, timedelta, timezone

from config import COUNTRY_DATA_PATH, SEED_HISTORY_COUNT
from model_utils import predict_hdi
from db_utils import init_db, clear_history, insert_prediction


def main():
    init_db()
    clear_history()

    with open(COUNTRY_DATA_PATH, "r") as f:
        countries = json.load(f)

    # Sample a spread across tiers rather than pure random, so the demo
    # history looks realistic (mix of very high / high / medium / low).
    by_tier = {}
    for c in countries:
        by_tier.setdefault(c["tier"], []).append(c)

    random.seed(7)
    for bucket in by_tier.values():
        random.shuffle(bucket)

    picks = []
    tiers = list(by_tier.keys())
    i = 0
    while len(picks) < SEED_HISTORY_COUNT:
        tier = tiers[i % len(tiers)]
        bucket = by_tier[tier]
        idx = (i // len(tiers)) % len(bucket)
        picks.append(bucket[idx])
        i += 1

    now = datetime.now(timezone.utc)
    # Oldest first so IDs increase chronologically; most recent ends up last.
    picks_chronological = list(reversed(picks))

    for offset, country in enumerate(picks_chronological):
        timestamp = now - timedelta(
            days=(len(picks_chronological) - offset) * 0.6,
            hours=random.randint(0, 20),
            minutes=random.randint(0, 59),
        )
        result = predict_hdi(
            country["life_exp"],
            country["expected_schooling"],
            country["mean_schooling"],
            country["gni"],
        )
        insert_prediction(
            label=country["country"],
            life_exp=country["life_exp"],
            expected_schooling=country["expected_schooling"],
            mean_schooling=country["mean_schooling"],
            gni=country["gni"],
            predicted_hdi=result["hdi"],
            predicted_tier=result["tier"],
            created_at=timestamp.isoformat(),
        )

    print(f"Seeded {len(picks_chronological)} demo predictions into the database.")


if __name__ == "__main__":
    main()
