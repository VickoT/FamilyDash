# components/washer_box.py
from dash import html, dcc, no_update
from datetime import datetime, timezone

# SVG: lägg till både appliance-svg (gemensam stil) och washer-svg (unika regler)
SVG_STRING = r"""
<svg class="appliance-svg washer-svg" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
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
    <path d="M23,38 c3,-3 6,-3 9,0 s6,3 9,0"
          fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
  </g>
</svg>
"""

# ---- Publikt API ---------------------------------------------------------
def box():
    """Wrapper för layouten."""
    # Starta med neutral tile tills första MQTT kommer
    children = _placeholder_children()
    klass = "box appliance-card washer-card"
    return html.Div(id="washer-box", className=klass, children=children)

def compute(snapshot: dict | None, tz, last_ts: dict | None):
    """
    snapshot['washer'] = {'ts': <epoch>, 'time_to_end_min': <int|float>}
    Returnerar (children|no_update, className|no_update, updated_last_ts)
    """
    last_ts = (last_ts or {}).copy()
    w = (snapshot or {}).get("washer") or {}
    ts = w.get("ts")

    # 1) Ingen data ännu → placeholder
    if not ts:
        return _placeholder_children(), "box appliance-card washer-card", last_ts

    # 2) De-dupe
    if last_ts.get("washer") == ts:
        return no_update, no_update, last_ts

    # 3) Ny data
    children, klass = _render(w, tz)
    last_ts["washer"] = ts
    return children, klass, last_ts

# ---- Interna helpers -----------------------------------------------------
def _placeholder_children():
    return [
        dcc.Markdown(SVG_STRING, dangerously_allow_html=True),
        html.Div("Venter på data …", className="time"),
    ]

def _render(w: dict, tz):
    minutes = w.get("time_to_end_min")
    try:
        minutes = int(minutes)
    except (TypeError, ValueError):
        minutes = 0

    running = minutes > 0
    ts = w.get("ts")

    if running:
        children = [
            dcc.Markdown(SVG_STRING, dangerously_allow_html=True),
            html.Div(_fmt_hhmm(minutes), className="value"),
        ]
        klass = "box appliance-card washer-card active"
    else:
        ts_str = _fmt_dt(ts, tz) if ts else "–"
        children = [
            dcc.Markdown(SVG_STRING, dangerously_allow_html=True),
            html.Div(ts_str, className="time"),
        ]
        klass = "box appliance-card washer-card"

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
