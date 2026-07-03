# Projekte

Monorepo mit mehreren selbst-gehosteten Dashboards und Tools. Jedes Projekt hat
seinen Backend-Code unter `apps/<projekt>/` und sein per GitHub Pages ausgeliefertes
Frontend unter `docs/<projekt>/`.

## Projekte

| Projekt | Status | Frontend | Code |
|---------|--------|----------|------|
| **Research Dashboard** | ✅ Live | [`docs/research-dashboard/`](docs/research-dashboard/) | [`apps/research-dashboard/`](apps/research-dashboard/) |
| **Portfolio Tracker** | 🚧 Im Aufbau | [`docs/portfolio-tracker/`](docs/portfolio-tracker/) | [`apps/portfolio-tracker/`](apps/portfolio-tracker/) |

Details je Projekt in dessen README:
[Research Dashboard](apps/research-dashboard/README.md) ·
[Portfolio Tracker](apps/portfolio-tracker/README.md)

## Ordnerstruktur

```
/
├─ apps/                         Backend-Code je Projekt
│  ├─ research-dashboard/        Datensammler (Python) + requirements + README
│  └─ portfolio-tracker/         Gerüst
├─ docs/                         GitHub Pages (eine Website)
│  ├─ index.html                 Landing-Page → verlinkt alle Projekte
│  ├─ research-dashboard/        Frontend + data/ (snapshot.json)
│  └─ portfolio-tracker/         Frontend (Platzhalter) + data/
└─ .github/workflows/            ein Workflow je Projekt
   ├─ research-dashboard.yml      täglicher Auto-Refresh
   └─ portfolio-tracker.yml       Gerüst (nur manuell startbar)
```

## GitHub Pages

Pages liefert den `docs/`-Ordner aus. Die öffentlichen Adressen:

- Übersicht: `https://<user>.github.io/<repo>/`
- Research Dashboard: `https://<user>.github.io/<repo>/research-dashboard/`
- Portfolio Tracker: `https://<user>.github.io/<repo>/portfolio-tracker/`

## Neues Projekt hinzufügen

1. `apps/<name>/` für den Code anlegen (Skript, `requirements.txt`, `README.md`).
2. `docs/<name>/` für das Frontend anlegen (`index.html`, ggf. `data/`).
3. In `docs/index.html` eine Karte für das neue Projekt ergänzen.
4. Bei Bedarf `.github/workflows/<name>.yml` für die Automatik hinzufügen.
