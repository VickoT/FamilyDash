# components/power_box.py
from dash import html, no_update
from datetime import datetime, timezone

def power_compute(snapshot, local_tz, last_ts):
    last_ts = last_ts or {}
    data = (snapshot or {}).get("pulse_power", {})
    ts = data.get("ts")

    if not ts:
        view = html.Div([
            html.Div("Elförbrukning", className="title"),
            html.Div("Väntar på data …", className="time"),
        ])
        return view, "box power-card", last_ts

    if last_ts.get("power") == ts:
        return no_update, no_update, last_ts

    power = data.get("power")
    ts_str = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(local_tz).strftime("%Y-%m-%d, %H:%M")
    power_txt = f"{power:.0f} W" if isinstance(power, (int, float)) else "– W"

    view = html.Div([
        html.Div("Strømforbrug", className="title"),
        html.Div([html.Span("⚡ "), html.Span(power_txt)], className="value"),
        html.Div(ts_str, className="kv-ts"),
    ])

    last_ts["power"] = ts
    return view, "box power-card", last_ts
