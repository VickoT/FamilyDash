# components/env_stue_box.py
from dash import html, no_update
from datetime import datetime, timezone

# Din tyngre emoji-serie 💀
EMOJI_BY_IAQ = {1: "😃", 2: "🙂", 3: "☹️", 4: "☠️", 5: "☠️☠️"}

def compute(snapshot, local_tz, last_ts):
    """
    Kombinerar Shelly BHT och VOC till en kompakt, ikonbaserad Stue-vy.
    Returnerar (view, box_class, last_ts).
    """
    last_ts = last_ts or {}
    bht = (snapshot or {}).get("shelly_bht", {})
    voc = (snapshot or {}).get("airquality_raw", {})

    ts_bht = bht.get("ts")
    ts_voc = voc.get("ts")
    ts_any = ts_voc or ts_bht

    if not ts_any:
        view = html.Div([
            html.Div("🏠 Stue", className="title"),
            html.Div("—", className="value"),
        ])
        return view, "box env-stue-card box--double", last_ts

    if last_ts.get("bht") == ts_bht and last_ts.get("voc") == ts_voc:
        return no_update, no_update, last_ts

    # --- data ---
    t  = bht.get("t")
    rh = bht.get("rh")
    tvoc = voc.get("tvoc_ppb")
    aqi  = voc.get("aqi")

    # --- format ---
    t_txt   = f"{t:.1f}°" if isinstance(t, (int, float)) else "–"
    rh_txt  = f"{rh:.0f}%" if isinstance(rh, (int, float)) else "–"
    voc_txt = f"{tvoc:.0f}" if isinstance(tvoc, (int, float)) else "–"
    emoji   = EMOJI_BY_IAQ.get(aqi, "🙂")

    ts_str = datetime.fromtimestamp(ts_any, tz=timezone.utc).astimezone(local_tz).strftime("%H:%M")

    # --- layout ---
    view = html.Div([
        html.Div(className="box__head", children=[
            html.Span("🏠 Stue", className="box__title"),
            html.Span(ts_str, className="box__time"),
        ]),
        html.Div(className="env-stue__grid", children=[
            html.Div(f"🌡️ {t_txt}", className="env-val"),
            html.Div(f"💧 {rh_txt}", className="env-val"),
            html.Div(f"VOC {voc_txt}", className=f"env-val iaq-{aqi if aqi else 0}"),
            html.Div(emoji, className="env-emoji"),
        ])
    ])

    box_class = "box env-stue-card box--double"
    if ts_bht: last_ts["bht"] = ts_bht
    if ts_voc: last_ts["voc"] = ts_voc

    return view, box_class, last_ts
