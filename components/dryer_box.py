# components/dryer_box.py
from dash import html, dcc, no_update
from datetime import datetime, timezone

# SVG får både appliance-svg (gemensam storlek/färg) och dryer-svg (unika regler)
SVG_STRING = r"""
<svg class="appliance-svg dryer-svg" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <g class="frame" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
    <rect x="5" y="7" width="54" height="50" rx="6"/>
    <line x1="5" y1="19" x2="59" y2="19"/>
  </g>
  <g class="panel" fill="currentColor">
    <circle class="panel-led" cx="14" cy="13" r="2.5"/>
    <rect class="panel-display" x="40" y="10" width="15" height="6" rx="2" ry="2"
          fill="none" stroke="currentColor" stroke-width="2"/>
  </g>
  <g class="door" style="transform-origin:32px 38px">
    <circle cx="32" cy="38" r="14" fill="none" stroke="currentColor" stroke-width="3"/>
    <circle cx="32" cy="38" r="9"  fill="none" stroke="currentColor" stroke-width="3"/>
  </g>
  <g class="fan" style="transform-origin:32px 38px" fill="currentColor">
    <circle cx="32" cy="38" r="1.6"/>
    <path id="blade" d="
      M32 38
      C 30.5 36.2, 32 34.0, 34.5 33.2
      C 37.0 32.5, 39.0 34.2, 39.5 36.0
      C 40.0 37.8, 38.5 39.8, 36.5 40.3
      C 34.5 40.8, 33.0 40.0, 32 38 Z" />
    <use href="#blade" transform="rotate(120 32 38)"/>
    <use href="#blade" transform="rotate(240 32 38)"/>
  </g>
  <g class="heat" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
    <path d="M47 32 q2 -3 4 0 t4 0" />
    <path d="M48.5 38 q2 -3 4 0 t4 0" />
    <path d="M47 44 q2 -3 4 0 t4 0" />
  </g>
</svg>
"""

def dryer_compute(snapshot: dict | None, tz, last_ts: dict | None):
    """
    snapshot['dryer'] = {
      'ts': <epoch>,
      'time_left': <int|min>   # minuter kvar; >0 = aktiv
    }
    Returnerar (children|no_update, className|no_update, updated_last_ts)
    """
    last_ts = (last_ts or {}).copy()
    d = (snapshot or {}).get("dryer") or {}
    ts = d.get("ts")

    # 1) Ingen data ännu → placeholder
    if not ts:
        return _placeholder_children(), "box appliance-card dryer-card", last_ts

    # 2) De-dupe: samma ts som senast → inga DOM-uppdateringar
    if last_ts.get("dryer") == ts:
        return no_update, no_update, last_ts

    # 3) Ny data → rendera och spara ts
    children, klass = _render(d, tz)
    last_ts["dryer"] = ts
    return children, klass, last_ts

# ---- Interna helpers ----------------------------------------------------
def _placeholder_children():
    return [
        dcc.Markdown(SVG_STRING, dangerously_allow_html=True),
        html.Div("Venter på data …", className="time"),
    ]

def _render(d: dict, tz):
    minutes = d.get("time_left")
    try:
        minutes = int(minutes)
    except (TypeError, ValueError):
        minutes = 0

    running = minutes > 0
    ts = d.get("ts")

    if running:
        children = [
            dcc.Markdown(SVG_STRING, dangerously_allow_html=True),
            html.Div(_fmt_hhmm(minutes), className="value"),
        ]
        klass = "box appliance-card dryer-card active"
    else:
        ts_str = _fmt_dt(ts, tz) if ts else "–"
        children = [
            dcc.Markdown(SVG_STRING, dangerously_allow_html=True),
            html.Div(ts_str, className="time"),
        ]
        klass = "box appliance-card dryer-card"

    return children, klass

def _fmt_dt(ts, tz):
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(tz).strftime("%Y-%m-%d, %H:%M")
    except Exception:
        return "–"

def _fmt_hhmm(total_min):
    try:
        m = int(total_min)
    except (TypeError, ValueError):
        return "–"
    if m < 0:
        m = 0
    h, mm = divmod(m, 60)
    return f"{h:02d}:{mm:02d}"
