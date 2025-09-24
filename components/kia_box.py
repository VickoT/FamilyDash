# components/kia_box.py
from dash import html, no_update
from datetime import datetime, timezone

def kia_compute(snapshot, local_tz, last_ts):
    last_ts = last_ts or {}
    kia = (snapshot or {}).get("kia", {})
    ts = kia.get("ts")

    # Inga data ännu
    if not ts:
        view = html.Div([
            html.Div("KIA"),
            html.Div("Venter på data …"),
        ])
        return view, "box kia-card", last_ts

    # Undvik onödiga re-renders
    if last_ts.get("kia") == ts:
        return no_update, no_update, last_ts

    ts_str = datetime.fromtimestamp(ts,
                                    tz=timezone.utc).astimezone(local_tz).strftime("%Y-%m-%d, %H:%M")

    battery = kia.get("battery")
    rng = kia.get("range")

    battery_txt = f"{battery:d} %" if isinstance(battery, int) else "– %"
    range_txt   = f"{rng:d} km"     if isinstance(rng, int)     else "– km"

    view = html.Div([
        html.Div("KIA"),
        html.Div([html.Span("🔋 "), f"{battery_txt}"]),
        html.Div([html.Span("🛣️ "), f"{range_txt}"]),
        html.Div(f"{ts_str}"),
    ])

    last_ts["kia"] = ts
    return view, "box kia-card", last_ts


