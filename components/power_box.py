# components/power_box.py
import time
from dash import html, no_update
from datetime import datetime, timezone

_STALE_SECONDS = 600  # 10 minutes

def power_compute(snapshot, local_tz, last_ts):
    last_ts = (last_ts or {}).copy()
    data = (snapshot or {}).get("pulse_power", {})
    ts = data.get("ts")

    if not ts:
        return html.Div("Väntar på data …", className="time"), "box appliance-card power-card", last_ts

    power_raw    = data.get("power_raw")
    power_smooth = data.get("power_smooth")
    energy_day   = data.get("energy_day_kwh")
    cost_day     = data.get("cost_day")

    ts_str = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(local_tz).strftime("%Y-%m-%d, %H:%M")
    stale = (time.time() - ts) > _STALE_SECONDS
    ts_style = {"color": "red", "fontWeight": "bold"} if stale else {}

    smooth_txt = f"⚡ {power_smooth:.0f} W"        if isinstance(power_smooth, (int, float)) else "⚡ – W"
    energy_txt = f"⚡ {energy_day:.2f} kWh"       if isinstance(energy_day,   (int, float)) else "⚡ – kWh"
    cost_txt   = f"💸 {cost_day:.2f} kr"          if isinstance(cost_day,     (int, float)) else "💸 –"

    view = html.Div([
        html.Ul([
            html.Li(smooth_txt),
            html.Li(energy_txt),
            html.Li(cost_txt),
        ], className="kv-list"),
        html.Div(ts_str, className="kv-ts", style=ts_style),
    ])

    return view, "box appliance-card power-card", last_ts
