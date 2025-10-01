# components/voc_box.py
from dash import html, no_update
from datetime import datetime, timezone

def voc_compute(snapshot, local_tz, last_ts):
    last_ts = last_ts or {}
    data = (snapshot or {}).get("airquality_raw", {})
    ts = data.get("ts")

    if not ts:
        view = html.Div([
            html.Div("Luftkvalitet", className="title"),
            html.Div("Väntar på data …", className="time"),
        ])
        return view, "box voc-card", last_ts

    if last_ts.get("voc") == ts:
        return no_update, no_update, last_ts

    tvoc = data.get("tvoc_ppb")
    aqi = data.get("aqi")
    ts_str = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(local_tz).strftime("%Y-%m-%d, %H:%M")
    voc_txt = f"{tvoc} ppb" if isinstance(tvoc, (int, float)) else "– ppb"

    view = html.Div([
        html.Div("TVOC", className="title"),
        html.Div([
            html.Span("💀  "),
            html.Span(voc_txt),
            html.Div(f"AQI: {aqi}" if isinstance(aqi, (int, float)) else "(AQI: –)"),
        ], className="value", style={"fontSize": "1.5rem", "fontWeight": "800"}),
        html.Div(ts_str, className="kv-ts"),
    ])

    last_ts["voc"] = ts
    return view, "box voc-card", last_ts
