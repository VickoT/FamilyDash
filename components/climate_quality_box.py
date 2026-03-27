# components/climate_quality_box.py
from dash import html, no_update
from datetime import datetime, timezone

def climate_quality_compute(snapshot, local_tz, last_ts):
    last_ts = (last_ts or {}).copy()

    bht = (snapshot or {}).get("shelly_bht", {})
    bht_ts = bht.get("ts")

    if not bht_ts:
        return html.Div("Väntar på data …", className="time"), "box climate-quality-card", last_ts

    if last_ts.get("bht") == bht_ts:
        return no_update, no_update, last_ts

    t = bht.get("t")
    rh = bht.get("rh")
    t_txt = f"{t:.1f} °C" if isinstance(t, (int, float)) else "– °C"
    rh_txt = f"{rh:.0f} %"  if isinstance(rh, (int, float)) else "– %"

    view = html.Div([
        html.Div("Stue", className="subtitle"),
        html.Div([html.Span("🌡️ "), html.Span(t_txt)], className="value"),
        html.Div([html.Span("💧 "), html.Span(rh_txt)], className="value"),
    ], className="climate-section")

    last_ts["bht"] = bht_ts
    return view, "box climate-quality-card", last_ts
