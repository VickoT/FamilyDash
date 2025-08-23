# components/washer_box.py
import os, math, pandas as pd
from dash import html, dcc
from datetime import datetime

CSV_PATH = os.getenv("WASHER_FILE", "data/washer_w.csv")

SVG_STRING = r"""
<svg class="washer-svg" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
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
    <path d="M22,38c3,-3 6,-3 10,0s7,3 10,0"
          fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
  </g>
</svg>
"""

def _read_washer():
    """Read last power value and timestamp from CSV."""
    w = float("nan"); ts_fmt = ""
    try:
        df = pd.read_csv(CSV_PATH, names=["ts", "W"])
        latest = df.iloc[-1]
        w = float(latest["W"])
        ts = str(latest["ts"])
        try:
            dt = datetime.fromisoformat(ts)
            ts_fmt = dt.strftime("%Y-%m-%d, %H:%M")
        except Exception:
            ts_fmt = ts
    except Exception as e:
        print(f"[washer_box] failed to read {CSV_PATH}: {e}")
    return w, ts_fmt

def washer_render():
    """Return children and classes for the washer box (only icon + timestamp)."""
    w, ts_fmt = _read_washer()
    active = (not math.isnan(w) and w > 0.0)

    classes = "box washer-card" + (" active" if active else "")

    children = [
        dcc.Markdown(SVG_STRING, dangerously_allow_html=True),
        html.Div(ts_fmt, className="time"),
    ]
    return children, classes

def washer_box():
    children, classes = washer_render()
    return html.Div(children=children, className=classes, id="washer-box")
