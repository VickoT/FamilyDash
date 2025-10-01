# components/voc_box.py
from dash import html, no_update
from datetime import datetime, timezone

EMOJI_BY_IAQ = {1: "😃", 2: "🙂", 3: "☹️", 4: "☠️", 5: "☠️☠️"}

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
    aqi = data.get("aqi")  # ENS160 IAQ: 1–5
    ts_str = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(local_tz).strftime("%Y-%m-%d, %H:%M")

    voc_txt = f"{tvoc} ppb" if isinstance(tvoc, (int, float)) else "– ppb"
    emoji = EMOJI_BY_IAQ.get(aqi, "🙂")

    view = html.Div([
        html.Div("TVOC", className="title"),
        html.Div(voc_txt, className=f"value iaq-{aqi}"),           # Värdet i ppb
        html.Div(emoji, className="emoji"),             # Emoji-raden
        html.Div(ts_str, className="timestamp"),            # Timestamp
    ], className="voc-inner")

    # Lägg iaq-klass för färgsättning i CSS
    box_class = f"box voc-card" if isinstance(aqi, (int, float)) else "box voc-card"

    last_ts["voc"] = ts
    return view, box_class, last_ts
