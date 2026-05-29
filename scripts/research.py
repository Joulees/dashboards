#!/usr/bin/env python3
"""
Research Dashboard — taeglicher Datensammler.

Laeuft im GitHub-Actions-Workflow (cron 07:00). Liest data/companies.json,
holt pro Titel Kurse / News / Earnings-Termine von Financial Modeling Prep (FMP),
berechnet technische Indikatoren, fasst optional via Anthropic-API zusammen und
schreibt das Ergebnis nach docs/data/snapshot.json (von GitHub Pages ausgeliefert).

Benoetigte Umgebungsvariablen (als GitHub-Secrets hinterlegen):
  FMP_API_KEY        – Pflicht. Kostenloser Key von financialmodelingprep.com
  ANTHROPIC_API_KEY  – Optional. Nur fuer KI-Zusammenfassungen der News.

Alles ist fehlertolerant: Faellt eine Quelle fuer einen Titel aus, bleibt der Rest
erhalten und das Skript laeuft weiter.
"""

import os
import sys
import json
import time
import math
import datetime as dt
import html as html_mod
import re
from xml.etree import ElementTree as ET
from urllib import request, parse, error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPANIES_FILE = os.path.join(ROOT, "docs", "data", "companies.json")
OUT_FILE = os.path.join(ROOT, "docs", "data", "snapshot.json")

FMP_KEY = os.environ.get("FMP_API_KEY", "").strip()
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
FMP_BASE = "https://financialmodelingprep.com/stable"
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")

TODAY = dt.date.today()
HORIZON_DAYS = 95           # Kurshistorie (Tage)
NEWS_LOOKBACK_DAYS = 21     # nur News der letzten N Tage
EVENT_HORIZON_DAYS = 100    # kommende Events bis N Tage


# ----------------------------- HTTP-Helfer -----------------------------
def http_get_json(url, tries=3, pause=1.5):
    """GET mit JSON-Antwort, einfache Retries."""
    for attempt in range(tries):
        try:
            req = request.Request(url, headers={"User-Agent": "research-dashboard/1.0"})
            with request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as e:
            if e.code == 429:                      # rate limit -> warten
                time.sleep(pause * (attempt + 1) * 2)
                continue
            print(f"   HTTP {e.code} bei {url.split('?')[0]}")
            return None
        except Exception as e:
            if attempt == tries - 1:
                print(f"   Fehler bei {url.split('?')[0]}: {e}")
                return None
            time.sleep(pause)
    return None


def http_get_text(url, tries=2, pause=1.0):
    """GET mit Text-Antwort (fuer RSS/XML)."""
    for attempt in range(tries):
        try:
            req = request.Request(url, headers={"User-Agent": "Mozilla/5.0 research-dashboard/1.0"})
            with request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", "replace")
        except Exception as e:
            if attempt == tries - 1:
                print(f"   RSS-Fehler bei {url.split('?')[0]}: {e}")
                return None
            time.sleep(pause)
    return None


def fmp(path, **params):
    params["apikey"] = FMP_KEY
    return http_get_json(f"{FMP_BASE}/{path}?{parse.urlencode(params)}")


# ----------------------------- FMP-Abrufe (stable API) -----------------------------
def get_prices(symbol):
    """Taegliche Schlusskurse (aelteste zuerst). Erst 'full', bei Sperre 'light'."""
    frm = (TODAY - dt.timedelta(days=HORIZON_DAYS * 2)).isoformat()
    to = TODAY.isoformat()
    for path, field in (("historical-price-eod/full", "close"),
                        ("historical-price-eod/light", "price")):
        data = fmp(path, symbol=symbol, **{"from": frm, "to": to})
        if isinstance(data, list) and data:
            rows = [d for d in data if d.get(field) is not None and d.get("date")]
            rows.sort(key=lambda d: d["date"])
            closes = [float(d[field]) for d in rows][-HORIZON_DAYS:]
            if len(closes) >= 20:
                return {"closes": closes}
    return None


def get_currency(symbol):
    prof = fmp("profile", symbol=symbol)
    if isinstance(prof, list) and prof:
        return prof[0].get("currency", "") or ""
    return ""


def _relevant(name, title, summary):
    """Behalte nur Meldungen, die den Firmennamen wirklich erwähnen."""
    hay = (title + " " + summary).lower()
    nm = name.lower()
    if nm in hay:
        return True
    # sonst: laengstes markantes Wort des Namens muss vorkommen
    words = [w for w in re.split(r"[^a-zA-ZäöüÄÖÜ0-9]+", nm) if len(w) >= 4]
    return any(w in hay for w in words) if words else False


def _fetch_rss(name, query, lang):
    if lang == "de":
        loc = "&hl=de&gl=DE&ceid=DE:de"
    else:
        loc = "&hl=en-US&gl=US&ceid=US:en"
    url = "https://news.google.com/rss/search?q=" + parse.quote(query + " when:21d") + loc
    xml = http_get_text(url)
    if not xml:
        return []
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return []
    from email.utils import parsedate_to_datetime
    out = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        desc = item.findtext("description") or ""
        try:
            date_iso = parsedate_to_datetime(pub).date().isoformat()
        except Exception:
            date_iso = TODAY.isoformat()
        source = ""
        if " - " in title:
            title, source = title.rsplit(" - ", 1)
        summary = re.sub(r"<[^>]+>", " ", html_mod.unescape(desc))
        summary = re.sub(r"\s+", " ", summary).strip()[:240]
        title = title.strip()
        if not _relevant(name, title, summary):
            continue
        out.append({"date": date_iso, "title": title,
                    "summary": summary or title,
                    "source": source.strip(), "url": link, "category": "Sonstiges"})
    return out


def get_news(name, query=None):
    """Kostenlose News via Google-News-RSS. Deutsch bevorzugt, Englisch als Ergaenzung."""
    q = query or f'"{name}"'
    items = _fetch_rss(name, q, "de")
    if len(items) < 3:                       # international oft nur englisch abgedeckt
        seen = {n["title"] for n in items}
        for n in _fetch_rss(name, q, "en"):
            if n["title"] not in seen:
                items.append(n); seen.add(n["title"])
    items.sort(key=lambda n: n["date"], reverse=True)
    return items[:6]


def get_events(symbol):
    """Kommende Earnings-Termine. Stable: /earnings-calendar?symbol=SYM&from&to"""
    frm = TODAY.isoformat()
    to = (TODAY + dt.timedelta(days=EVENT_HORIZON_DAYS)).isoformat()
    data = fmp("earnings-calendar", symbol=symbol, **{"from": frm, "to": to})
    out = []
    if isinstance(data, list):
        for e in data:
            date_str = (e.get("date") or "")[:10]
            if date_str >= frm:
                out.append({"date": date_str, "title": "Earnings / Quartalszahlen", "type": "Earnings"})
    return out[:4]


# ----------------------------- Technische Analyse -----------------------------
def sma(a, n):
    return sum(a[-n:]) / n if len(a) >= n else None


def ema_series(a, n):
    if not a:
        return []
    k = 2 / (n + 1)
    out = [a[0]]
    for i in range(1, len(a)):
        out.append(a[i] * k + out[-1] * (1 - k))
    return out


def rsi(a, n=14):
    if len(a) < n + 1:
        return None
    g = l = 0.0
    for i in range(len(a) - n, len(a)):
        d = a[i] - a[i - 1]
        if d >= 0:
            g += d
        else:
            l -= d
    if l == 0:
        return 100.0
    rs = (g / n) / (l / n)
    return 100 - 100 / (1 + rs)


def macd(a):
    if len(a) < 26:
        return None
    e12, e26 = ema_series(a, 12), ema_series(a, 26)
    line = [e12[i] - e26[i] for i in range(len(a))]
    sig = ema_series(line[25:], 9)
    return {"line": line[-1], "signal": sig[-1]}


def bollinger(a, n=20, k=2):
    if len(a) < n:
        return None
    s = a[-n:]
    m = sum(s) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in s) / n)
    return {"mid": m, "upper": m + k * sd, "lower": m - k * sd}


def compute_ta(closes, currency=""):
    if not closes or len(closes) < 20:
        return None
    price = closes[-1]
    s50, s200 = sma(closes, 50), sma(closes, 200)
    r, m, bb = rsi(closes), macd(closes), bollinger(closes)
    score, reasons = 0, []
    if s50 is not None:
        if price > s50: score += 1; reasons.append("Kurs ueber SMA50")
        else: score -= 1; reasons.append("Kurs unter SMA50")
    if s200 is not None:
        if price > s200: score += 1; reasons.append("Kurs ueber SMA200")
        else: score -= 1; reasons.append("Kurs unter SMA200")
    if m:
        if m["line"] > m["signal"]: score += 1; reasons.append("MACD ueber Signallinie")
        else: score -= 1; reasons.append("MACD unter Signallinie")
    if r is not None:
        if r > 70: score -= 1; reasons.append("RSI ueberkauft (>70)")
        elif r < 30: score += 1; reasons.append("RSI ueberverkauft (<30)")
    if bb:
        if price > bb["upper"]: score -= 1; reasons.append("ueber oberem Bollinger-Band")
        elif price < bb["lower"]: score += 1; reasons.append("unter unterem Bollinger-Band")
    label = "Bullisch" if score >= 2 else "Baerisch" if score <= -2 else "Neutral"
    return {
        "currency": currency, "closes": closes,
        "price": round(price, 2),
        "sma50": round(s50, 2) if s50 else None,
        "sma200": round(s200, 2) if s200 else None,
        "rsi": round(r) if r is not None else None,
        "macd": "bullisch" if m and m["line"] > m["signal"] else ("baerisch" if m else None),
        "high": round(max(closes), 2), "low": round(min(closes), 2),
        "score": score, "label": label, "reasons": reasons,
    }


# ----------------------------- Anthropic-Summary (optional) -----------------------------
def summarize_news(name, news):
    """Verdichtet Roh-News zu kurzen deutschen Summaries + Kategorie. Optional."""
    if not ANTHROPIC_KEY or not news:
        # Fallback: gekuerzte Originaltexte ohne KI
        for n in news:
            n["summary"] = (n["summary"] or "")[:220]
        return news
    items = [{"title": n["title"], "text": n["summary"][:300]} for n in news]
    prompt = (
        f'Fasse folgende Meldungen zum Unternehmen "{name}" jeweils in EINEM deutschen Satz '
        f'zusammen und ordne eine Kategorie zu (Earnings, Conference, Guidance, M&A, Rating, '
        f'Markt oder Sonstiges). Antworte NUR als JSON-Array in identischer Reihenfolge: '
        f'[{{"summary":"...","category":"..."}}]. Meldungen: {json.dumps(items, ensure_ascii=False)}'
    )
    try:
        body = json.dumps({
            "model": ANTHROPIC_MODEL,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")
        req = request.Request(
            "https://api.anthropic.com/v1/messages", data=body, method="POST",
            headers={"content-type": "application/json", "x-api-key": ANTHROPIC_KEY,
                     "anthropic-version": "2023-06-01"})
        with request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        text = text.replace("```json", "").replace("```", "").strip()
        arr = json.loads(text[text.index("["): text.rindex("]") + 1])
        for i, n in enumerate(news):
            if i < len(arr):
                n["summary"] = arr[i].get("summary", n["summary"])[:300]
                cat = arr[i].get("category", "Sonstiges")
                valid = {"Earnings", "Conference", "Guidance", "M&A", "Rating", "Markt", "Sonstiges"}
                n["category"] = cat if cat in valid else "Sonstiges"
    except Exception as e:
        print(f"   Summary-Fallback ({name}): {e}")
        for n in news:
            n["summary"] = (n["summary"] or "")[:220]
    return news


# ----------------------------- Hauptlauf -----------------------------
def main():
    if not FMP_KEY:
        print("FEHLER: FMP_API_KEY ist nicht gesetzt. Abbruch.")
        sys.exit(1)

    with open(COMPANIES_FILE, encoding="utf-8") as f:
        companies = json.load(f)

    snapshot = {
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "companies": {}, "news": [], "events": [],
    }

    for c in companies:
        cid, name, sym = c["id"], c["name"], c.get("symbol")
        print(f"-> {name} ({sym or 'kein Symbol'})")
        entry = {"news": [], "events": [], "tech": None,
                 "profile": {"businessModel": "", "differentiation": ""}}

        # News: kostenlos via Google-News-RSS — fuer ALLE Titel, auch ohne Symbol
        raw_news = get_news(name, c.get("newsQuery"))
        raw_news = summarize_news(name, raw_news)
        for n in raw_news:
            n.update({"companyId": cid, "company": name,
                      "asset": c["asset"], "status": c["status"]})
        entry["news"] = raw_news
        snapshot["news"].extend(raw_news)

        # Kurse + Events: nur bei vorhandenem FMP-Symbol
        if sym:
            prices = get_prices(sym)
            if prices and not c.get("noChart"):
                entry["tech"] = compute_ta(prices["closes"], get_currency(sym))
            for e in get_events(sym):
                e.update({"companyId": cid, "company": name})
                entry["events"].append(e)
                snapshot["events"].append(e)
            time.sleep(0.3)   # FMP schonen

        snapshot["companies"][str(cid)] = entry

    snapshot["news"].sort(key=lambda n: n.get("date", ""), reverse=True)
    snapshot["events"].sort(key=lambda e: e.get("date", ""))

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=1)

    print(f"\nFertig: {len(snapshot['news'])} News, {len(snapshot['events'])} Events "
          f"-> {os.path.relpath(OUT_FILE, ROOT)}")

    have_tech = sum(1 for e in snapshot["companies"].values() if e.get("tech"))
    print(f"Kursdaten vorhanden fuer {have_tech} Titel.")
    if len(snapshot["news"]) == 0 and have_tech == 0:
        print("HINWEIS: Es kamen keinerlei Daten zurueck. Pruefe (1) ob FMP_API_KEY gueltig ist "
              "und (2) ob dein FMP-Plan die Endpunkte abdeckt. News/Earnings koennen je nach Plan "
              "eingeschraenkt sein; Kurse sind im Free-Plan i.d.R. verfuegbar.")


if __name__ == "__main__":
    main()
