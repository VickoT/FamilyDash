# components/bht_box.py
from dash import html, no_update
from datetime import datetime, timezone

def bht_compute(snapshot, local_tz, last_ts):
    last_ts = last_ts or {}
    bht = (snapshot or {}).get("shelly_bht", {})
    ts  = bht.get("ts")

    if not ts:
        view = html.Div([
            html.Div("Shelly-BHT", className="title"),
            html.Div("Väntar på data …", className="time"),
        ])
        return view, "box climate-card", last_ts

    if last_ts.get("bht") == ts:
        return no_update, no_update, last_ts

    t  = bht.get("t")
    rh = bht.get("rh")
    ts_str = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(local_tz).strftime("%Y-%m-%d, %H:%M")

    t_txt  = f"{t:.1f} °C" if isinstance(t, (int, float)) else "– °C"
    rh_txt = f"{rh:.0f} %"  if isinstance(rh, (int, float)) else "– %"

    view = html.Div([
        html.Div("Stue", className="title"),
        html.Div([html.Span("🌡️ "), html.Span(t_txt)], className="value"),
        html.Div([html.Span("💧 "), html.Span(rh_txt)], className="value"),
        html.Div(ts_str, className="kv-ts"),
    ])

    last_ts["bht"] = ts
    return view, "box climate-card", last_ts
