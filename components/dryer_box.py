# components/dryer_box.py
from dash import html, no_update
from datetime import datetime, timezone

def compute(snapshot: dict | None, tz, last_ts: dict | None):
    last_ts = (last_ts or {}).copy()
    d = (snapshot or {}).get("dryer") or {}

    # normaliser status
    raw_status = d.get("status")
    status = (raw_status or "").strip().lower()
    minutes = d.get("time_left")
    try:
        minutes = int(minutes)
    except (TypeError, ValueError):
        minutes = None

    ts = d.get("ts")
    fp = (ts, status, minutes)

    if ts is None and last_ts.get("dryer_fp") is None:
        return _placeholder(), "tile", last_ts

    if last_ts.get("dryer_fp") == fp:
        return no_update, no_update, last_ts

    children, klass = _render(status, minutes, ts, tz)
    last_ts["dryer_fp"] = fp
    return children, klass, last_ts

# ---------- intern render ----------

def _render(status: str, minutes: int | None, ts, tz):
    running = (status != "none")

    if running and (isinstance(minutes, int) and minutes > 0):
        time_line = html.Div(f"Tid tilbage: {_fmt_hhmm(minutes)}")
    else:
        time_line = html.Div("Tid tilbage: –")

    ts_str = _fmt_ts(ts, tz) if ts is not None else "–"

    view = html.Div([
        html.Div("Tørretumbler"),
        html.Div(f"Status: {status or 'ukendt'}"),
        time_line,
        html.Div(f"Senest: {ts_str}"),
    ])
    klass = "tile active" if running else "tile"
    return view, klass

def _placeholder():
    return html.Div([html.Div("Tørretumbler"), html.Div("Venter på data …")])

def _fmt_hhmm(total_min: int) -> str:
    if total_min is None or total_min < 0:
        return "00:00"
    h, m = divmod(int(total_min), 60)
    return f"{h:02d}:{m:02d}"

def _fmt_ts(ts, tz):
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(tz).strftime("%H:%M:%S")
    except Exception:
        return "–"
