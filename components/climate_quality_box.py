# components/climate_quality_box.py
from dash import html, no_update
from datetime import datetime, timezone

EMOJI_BY_IAQ = {1: "😃", 2: "🙂", 3: "☹️", 4: "☠️", 5: "☠️☠️"}

def climate_quality_compute(snapshot, local_tz, last_ts):
    """Combined widget: Climate (temp/humidity) + Air Quality (TVOC/AQI)"""
    last_ts = last_ts or {}

    # Get both data sources
    bht = (snapshot or {}).get("shelly_bht", {})
    airquality = (snapshot or {}).get("airquality_raw", {})

    bht_ts = bht.get("ts")
    voc_ts = airquality.get("ts")

    # Check if we have any data at all
    if not bht_ts and not voc_ts:
        view = html.Div([
            html.Div("Stue Klimat", className="title"),
            html.Div("Väntar på data …", className="time"),
        ])
        return view, "box climate-quality-card", last_ts

    # Check for updates (de-duplication)
    if last_ts.get("bht") == bht_ts and last_ts.get("voc") == voc_ts:
        return no_update, no_update, last_ts

    # Extract climate data
    t = bht.get("t")
    rh = bht.get("rh")
    t_txt = f"{t:.1f} °C" if isinstance(t, (int, float)) else "– °C"
    rh_txt = f"{rh:.0f} %" if isinstance(rh, (int, float)) else "– %"

    # Extract air quality data
    tvoc = airquality.get("tvoc_ppb")
    aqi = airquality.get("aqi")
    tvoc_value = f"{tvoc}" if isinstance(tvoc, (int, float)) else "–"
    emoji = EMOJI_BY_IAQ.get(aqi, "🙂")

    # Format VOC timestamp
    voc_ts_str = ""
    if voc_ts:
        voc_ts_str = datetime.fromtimestamp(voc_ts, tz=timezone.utc).astimezone(local_tz).strftime("%Y-%m-%d, %H:%M")

    # Build combined view
    view = html.Div([
        # Top section: Climate
        html.Div([
            html.Div("Stue", className="subtitle"),
            html.Div([html.Span("🌡️ "), html.Span(t_txt)], className="value"),
            html.Div([html.Span("💧 "), html.Span(rh_txt)], className="value"),
        ], className="climate-section"),

        # Bottom section: Air Quality
        html.Div([
            html.Div([
                html.Span("VOC ", className="voc-label"),
                html.Span(tvoc_value, className=f"voc-value iaq-{aqi}"),
                html.Span(" ppb", className="voc-label"),
            ], className="value"),
            html.Div(emoji, className="emoji"),
            html.Div(voc_ts_str, className="timestamp") if voc_ts_str else None,
        ], className="airquality-section"),
    ])

    # Update timestamps
    if bht_ts:
        last_ts["bht"] = bht_ts
    if voc_ts:
        last_ts["voc"] = voc_ts

    return view, "box climate-quality-card", last_ts
