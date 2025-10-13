# components/calendar_box.py
from dash import html
from datetime import date, datetime, timedelta
from typing import Dict, List, Any
import re
from mqtt_subscriber import get_snapshot

# --- Hjälpvariabler -----------------------------------------------------
_DA_WD  = ["Man", "Tir", "Ons", "Tor", "Fre", "Lør", "Søn"]
_DA_MON = ["Jan", "Feb", "Mar", "Apr", "Maj", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dec"]

# --- Hjälpfunktioner ----------------------------------------------------
def _is_sunday(label: str) -> bool:
    lab = (label or "").strip().lower()
    return lab.startswith(("søn", "sön", "sun"))

def _fmt_label(d: date) -> str:
    return f"{_DA_WD[d.weekday()]} {d.day:02d}/{_DA_MON[d.month-1]}"

def _norm_start_fields(ev: Dict[str, Any]) -> tuple[bool, str | None, str | None]:
    """Returnera (all_day, date_str, datetime_str) för olika start-format."""
    s = ev.get("start")
    if isinstance(s, dict):
        if "date" in s:
            return True, s.get("date"), None
        if "dateTime" in s and isinstance(s["dateTime"], str):
            return False, s["dateTime"][:10], s["dateTime"]
    elif isinstance(s, str):
        if "T" in s:
            return False, s[:10], s
        return True, s, None
    return False, None, None

def _event_time(ev: Dict[str, Any]) -> str | None:
    """Returnera bara starttid i HH:MM-format."""
    all_day, _date_str, dt_str = _norm_start_fields(ev)
    if all_day or not dt_str:
        return None
    try:
        sd = datetime.fromisoformat(dt_str)
        return sd.strftime("%H:%M")
    except Exception:
        return None

def _parse_date_str(ev: Dict[str, Any]) -> date | None:
    _all_day, dstr, dtstr = _norm_start_fields(ev)
    raw = dtstr or dstr
    if not raw:
        return None
    try:
        return datetime.strptime(raw[:10], "%Y-%m-%d").date()
    except Exception:
        return None

# --- Huvudfunktion ------------------------------------------------------
def calendar_box(path=None):  # path ignoreras, bibehåller signatur
    snap = get_snapshot()
    cal = (snap.get("calendar") or {})
    fam = (cal.get("familie") or {}).get("events_next7d") or []
    bday370 = (cal.get("fodelsedagar") or {}).get("events_next370d") or []

    today = date.today()
    end = today + timedelta(days=7)

    # Filtrera födelsedagar till nästa 7 dagar
    bday = [e for e in bday370 if (d := _parse_date_str(e)) and today <= d <= end]

    # Gruppera alla händelser per dag
    by_day: Dict[date, List[Dict[str, Any]]] = {}
    for ev in fam + bday:
        d = _parse_date_str(ev)
        if not d:
            continue
        by_day.setdefault(d, []).append(ev)

    # Bygg veckans dagar
    days = []
    for i in range(7):
        d = today + timedelta(days=i)
        events = by_day.get(d, [])
        mapped = [{"time": _event_time(ev), "title": ev.get("summary", "")} for ev in events]
        days.append({"label": _fmt_label(d), "events": mapped})

    # --- Render (samma HTML/CSS som tidigare) ----------------------------
    boxes = []
    for i, day in enumerate(days):
        label = day.get("label", "")
        events = day.get("events", [])
        title_cls = "day-label sunday" if _is_sunday(label) else "day-label"

        items = []
        if events:
            events = sorted(events, key=lambda e: (e.get("time") is None, e.get("time") or ""))
            for e in events:
                t = e.get("time")
                title = e.get("title", "").strip()

                # --- Födelsedagar --------------------------------------
                m = re.match(r"^([\wÅÄÖåäö\-]+)[^,]*,\s*(\d{4})$", title)
                if m:
                    name, year = m.groups()
                    try:
                        age = date.today().year - int(year)
                        title = f"{name} – {age} år!"
                    except Exception:
                        title = name
                    items.append(
                        html.Li(title, style={"color": "#ff66b2", "font-weight": "600"})
                    )
                    continue

                # --- Tömning tunna -------------------------------------
                if "tömning tunna" in title.lower():
                    items.append(
                        html.Li(
                            f"{t} - {title}" if t else title,
                            style={"color": "#5ecf64", "font-weight": "600"},
                        )
                    )
                    continue

                # --- Vanliga events ------------------------------------
                items.append(html.Li(f"{t} - {title}" if t else title))

        boxes.append(
            html.Div(
                className=f"day{' today' if i == 0 else ''}",
                children=[
                    html.Div(label, className=title_cls),
                    html.Ul(items, className="events"),
                ],
            )
        )

    return boxes
