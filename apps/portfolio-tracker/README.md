# Portfolio Tracker

**Status: 🚧 im Aufbau (Gerüst)**

Geplanter Überblick über Portfolio-Positionen, Allokation und Performance.

## Struktur

```
apps/portfolio-tracker/
├─ scripts/tracker.py       ← Datensammler (noch nicht implementiert)
├─ requirements.txt
└─ README.md                ← diese Datei

docs/portfolio-tracker/      ← von GitHub Pages ausgeliefert
├─ index.html               ← Frontend (Platzhalter)
└─ data/                    ← Snapshot-Ausgabe des Skripts
```

## Nächste Schritte

1. `scripts/tracker.py` implementieren: Positionen einlesen, Kurse holen,
   `docs/portfolio-tracker/data/snapshot.json` schreiben.
2. Frontend in `docs/portfolio-tracker/index.html` aufbauen (liest den Snapshot).
3. Automatik anlegen: `.github/workflows/portfolio-tracker.yml` erstellen
   (analog zu `research-dashboard.yml` mit `schedule` + `workflow_dispatch`).
   Bis dahin existiert bewusst kein Workflow für dieses Projekt.
