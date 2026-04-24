from __future__ import annotations

import csv
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent


def load_seed_csv(filename: str) -> list[dict[str, str]]:
    path = DATA_DIR / filename
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_teachers_seed() -> list[dict[str, str]]:
    return load_seed_csv("seed_teachers.csv")
