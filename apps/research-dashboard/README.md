# Research Dashboard

Ein selbst-gehostetes Research-Dashboard für Portfolio- und Watchlist-Unternehmen:
Newsflow, Event-Kalender, Märkte-Übersicht, Einzeltitel-Deep-Dive und technische Analyse.

Die Daten werden **täglich automatisch** über GitHub Actions gesammelt
(Kurse, News, Earnings-Termine von Financial Modeling Prep) und als `snapshot.json`
abgelegt. Das Frontend (eine einzige HTML-Datei) liest nur diesen Snapshot — schnell,
kostenlos, ohne Server.

```
GitHub Actions (cron)  ──►  apps/research-dashboard/scripts/research.py  ──►  docs/research-dashboard/data/snapshot.json
                                        │                                              │
                                   FMP + (optional) Anthropic                          ▼
                                                              GitHub Pages  ──►  docs/research-dashboard/index.html
```

> Dieses Projekt ist Teil eines Monorepos mit mehreren Projekten. Die Repo-Übersicht
> steht in der [README im Repo-Root](../../README.md).

---

## Was du brauchst

1. Einen **GitHub-Account** (hast du).
2. Einen **kostenlosen FMP-API-Key**: https://site.financialmodelingprep.com → registrieren → Dashboard → API-Key kopieren. Der Free-Plan erlaubt 250 Anfragen/Tag (genug für ~37 Titel).
3. *(Optional)* Einen **Anthropic-API-Key** für KI-Zusammenfassungen der News. Ohne diesen Key werden die Original-Kurztexte verwendet.

---

## Einrichtung

Das Repo ist bereits eingerichtet. Für einen Neuaufbau von Grund auf:

### 1. API-Keys als Secrets hinterlegen
- Im Repo: **Settings → Secrets and variables → Actions → New repository secret**.
- Secret 1: Name `FMP_API_KEY`, Wert = dein FMP-Key. **Add secret**.
- *(Optional)* Secret 2: Name `ANTHROPIC_API_KEY`, Wert = dein Anthropic-Key.

### 2. GitHub Pages aktivieren
- **Settings → Pages**.
- Unter „Build and deployment“: Source = **Deploy from a branch**.
- Branch = **main**, Ordner = **/docs**. **Save**.
- Nach ein paar Minuten zeigt die Seite oben die öffentliche Adresse. Die Projekt-Übersicht
  liegt unter `https://DEINNAME.github.io/<repo>/`, dieses Dashboard unter
  `https://DEINNAME.github.io/<repo>/research-dashboard/`.

### 3. Ersten Daten-Lauf manuell starten
- **Actions** → links „Taeglicher Research-Refresh“ → rechts **Run workflow → Run workflow**.
- Der Lauf dauert 1–3 Minuten. Danach ist `docs/research-dashboard/data/snapshot.json` mit echten Daten gefüllt.
- Dashboard-Seite neu laden — die Daten erscheinen.

### 4. Fertig
Ab jetzt läuft der Refresh **automatisch nach Zeitplan**. Du musst nichts mehr tun.
Zum manuellen Aktualisieren: entweder im Dashboard „↻ Neu laden“ (lädt den letzten Snapshot)
oder in **Actions** erneut „Run workflow“ (holt frische Daten sofort).

---

## Unternehmen bearbeiten

Im Dashboard unter **⚙ Einstellungen → Auswahl Unternehmen**:
- Titel anlegen, bearbeiten, löschen; Wettbewerber und Endmärkte pflegen.
- Wichtig pro Titel: das **FMP-Ticker-Symbol** (z. B. `MTRO.L`, `AMZN`, `MIN.AX`) — danach holt der Refresh Kurse/News.
- Änderungen wirken sofort lokal im Browser. Damit der **tägliche Refresh** sie nutzt:
  1. **„↓ companies.json herunterladen“** klicken.
  2. Die Datei im Repo unter `docs/research-dashboard/data/companies.json` ersetzen
     (im Repo die Datei öffnen → Stift-Symbol → alten Inhalt durch neuen ersetzen → Commit,
     oder per **Upload files** überschreiben).
- Der nächste Lauf berücksichtigt die neue Liste automatisch.

---

## Zeitzone der Automatik

GitHub-Cron läuft in **UTC**. Der Zeitplan steht in
`.github/workflows/research-dashboard.yml` (zwei Läufe: `17 0` und `17 2` UTC,
also ~02:00 Ortszeit mit Backup-Lauf). Passe die Cron-Zeilen dort an, wenn du eine
andere Uhrzeit möchtest.

---

## Ehrliche Grenzen

- **Datenabdeckung:** Der FMP-Free-Plan deckt US-Titel sehr gut ab, internationale Börsen
  (ASX, LSE, Wien, Mailand, Toronto) teils lückenhaft. Bei einzelnen Titeln können Kurse,
  News oder Termine fehlen — das Dashboard zeigt dann „keine Daten“ und bleibt im Übrigen
  voll funktionsfähig. Für lückenlose internationale Abdeckung wäre der FMP-Starter-Plan
  (~19 $/Monat) nötig.
- **News & Earnings-Kalender:** Einige FMP-Endpunkte können je nach Plan eingeschränkt sein.
  Kurse/technische Analyse funktionieren auf dem Free-Plan am zuverlässigsten.
- **IR-Events:** Aktuell aus dem FMP-Earnings-Kalender. Weitere IR-Termine (Hauptversammlung,
  Capital Markets Day) lassen sich später ergänzen, indem man im Skript pro Titel die
  IR-Seite ausliest — das ist seitenindividuell und nicht im Free-Setup enthalten.
- **Technisches Signal** ist eine mechanische Lesart der Indikatoren (SMA/RSI/MACD/Bollinger),
  **keine Anlageempfehlung**.

---

## Dateien im Überblick

| Datei | Zweck |
|-------|-------|
| `docs/research-dashboard/index.html` | Das komplette Dashboard (Frontend), wird von GitHub Pages ausgeliefert. |
| `docs/research-dashboard/data/companies.json` | Universum (Titel, Symbole, Peers, Endmärkte). Einzige Quelle, von Skript und Frontend gelesen. |
| `docs/research-dashboard/data/snapshot.json` | Täglich erzeugter Datenstand (News, Events, Kurse, Indikatoren). |
| `apps/research-dashboard/scripts/research.py` | Sammler-Skript (FMP-Abruf, TA-Berechnung, optionale KI-Summary). |
| `.github/workflows/research-dashboard.yml` | Zeitsteuerung (cron) + Commit des Snapshots. |
| `apps/research-dashboard/requirements.txt` | Nur Doku — das Skript nutzt ausschließlich die Python-Standardbibliothek. |
