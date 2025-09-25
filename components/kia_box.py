# components/kia_box.py
from dash import html, dcc, no_update
from datetime import datetime, timezone

KIA_SVG = r"""
<svg class="kia-title-svg" viewBox="0 0 120 28" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <text x="50%" y="50%" text-anchor="middle" dominant-baseline="middle"
        font-size="19" font-weight="700"
        font-family="system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', Arial, 'Noto Sans'"
        fill="currentColor" letter-spacing=".12em">KIA</text>
</svg>
"""

def kia_compute(snapshot, local_tz, last_ts):
    last_ts = last_ts or {}
    kia = (snapshot or {}).get("car", {})
    ts = kia.get("ts")

    if not ts:
        view = html.Div([
            dcc.Markdown(KIA_SVG, dangerously_allow_html=True),
            html.Div("Venter på data …", className="time"),
        ])
        return view, "box appliance-card kia-card", last_ts

    if last_ts.get("car") == ts:
        return no_update, no_update, last_ts

    ts_str = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(local_tz).strftime("%Y-%m-%d, %H:%M")
    battery = kia.get("battery"); rng = kia.get("range")
    battery_txt = f"{battery:d} %" if isinstance(battery, int) else "– %"
    range_txt   = f"{rng:d} km"     if isinstance(rng, int)     else "– km"

    view = html.Div([
        dcc.Markdown(KIA_SVG, dangerously_allow_html=True),
        html.Div([html.Span("🔋 "), html.Span(battery_txt)], className="value"),
        html.Div([html.Span("🛣️ "), html.Span(range_txt)],   className="value"),
        html.Div(ts_str, className="kv-ts"),
    ])

    last_ts["car"] = ts
    return view, "box appliance-card kia-card", last_ts
