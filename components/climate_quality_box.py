# components/climate_quality_box.py
from dash import html, no_update
from datetime import datetime, timezone
import time

_STALE_SECONDS = 4 * 3600  # 4 hours


def climate_quality_compute(snapshot, local_tz, last_ts):
    last_ts = (last_ts or {}).copy()

    bht = (snapshot or {}).get("shelly_bht", {})
    bht_ts = bht.get("ts")

    if not bht_ts:
        return html.Div("Väntar på data …", className="time"), "box climate-quality-card", last_ts

    stale = (time.time() - bht_ts) > _STALE_SECONDS

    if last_ts.get("bht") == bht_ts and last_ts.get("bht_stale") == stale:
        return no_update, no_update, last_ts

    t = bht.get("t")
    rh = bht.get("rh")
    t_txt = f"{t:.1f} °C" if isinstance(t, (int, float)) else "– °C"
    rh_txt = f"{rh:.0f} %"  if isinstance(rh, (int, float)) else "– %"

    ts_str = datetime.fromtimestamp(bht_ts, tz=timezone.utc).astimezone(local_tz).strftime("%Y-%m-%d, %H:%M")
    ts_class = "timestamp wx-ts-stale" if stale else "timestamp"

    view = html.Div([
        html.Div("Stue", className="subtitle"),
        html.Div([html.Span("🌡️ "), html.Span(t_txt)], className="value"),
        html.Div([html.Span("💧 "), html.Span(rh_txt)], className="value"),
        html.Div(ts_str, className=ts_class),
    ], className="climate-section")

    last_ts["bht"] = bht_ts
    last_ts["bht_stale"] = stale
    return view, "box climate-quality-card", last_ts
