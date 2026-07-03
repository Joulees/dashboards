#!/usr/bin/env python3
"""
Portfolio Tracker — Datensammler (Geruest).

Noch nicht implementiert. Analog zum Research-Dashboard soll dieses Skript
spaeter die Portfolio-Positionen einlesen, aktuelle Kurse holen und einen
Snapshot nach docs/portfolio-tracker/data/snapshot.json schreiben, den das
Frontend (docs/portfolio-tracker/index.html) ausliest.

Basispfad-Konvention (wie im Research-Dashboard):
  Skript liegt in apps/portfolio-tracker/scripts/ ; die Daten liegen im
  gemeinsamen docs/portfolio-tracker/data/ (von GitHub Pages ausgeliefert).
"""

import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DATA_DIR = os.path.join(REPO_ROOT, "docs", "portfolio-tracker", "data")
OUT_FILE = os.path.join(DATA_DIR, "snapshot.json")


def main() -> None:
    raise SystemExit("Portfolio Tracker: noch nicht implementiert.")


if __name__ == "__main__":
    main()
