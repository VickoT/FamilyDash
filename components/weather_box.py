# components/weather_box.py
import os, json
from pathlib import Path
from dash import html
from datetime import datetime

# Always resolve .../data/weather.json relative to the project root
BASE_DIR = Path(__file__).resolve().parents[1]
JSON_PATH = Path(os.getenv("WEATHER_FILE", str(BASE_DIR / "data" / "weather.json")))

def uv_bucket(v):
    """Return (class_suffix, Danish label) for a UV value."""
    if not isinstance(v, (int, float)):
        return "unknown", "–"
    if v <= 2:   return "low",        "Lav"
    if v <= 5:   return "medium",     "Moderat"
    if v <= 7:   return "high",       "Høj"
    if v <= 10:  return "very-high",  "Meget høj"
    return "extreme", "Ekstrem"

def uv_class(v):
    """Return full CSS class for the UV span."""
    b, _ = uv_bucket(v)
    return f"uv uv-{b}"

def weather_box():
    try:
        with open(JSON_PATH, encoding="utf-8") as f:
            data = json.load(f)

        # Parsed payload sections
        cur   = data.get("current", {})  # {"temperature": ..., "icon": ...}
        today = data.get("today", {})    # {"t_max": ..., "uv_max": ..., "precip_sum_mm": ..., "precip_prob_max": ..., "icon": ...}
        gen   = data.get("generated_at")

        # Raw values
        icon = (today.get("icon") or cur.get("icon") or "🌡️")
        now  = cur.get("temperature")
        tmax = today.get("t_max")
        uv   = today.get("uv_max")
        rain = today.get("precip_sum_mm")
        prob = today.get("precip_prob_max")

        # Display texts
        now_txt  = f"{now:.0f}°C"   if isinstance(now,  (int, float)) else "–°C"
        tmax_txt = f"{tmax:.0f}°C"  if isinstance(tmax, (int, float)) else "–°C"
        uv_txt   = f"{uv:.0f}"      if isinstance(uv,   (int, float)) else "–"
        rain_txt = f"{rain:.1f} mm" if isinstance(rain, (int, float)) else "0 mm"
        prob_txt = f"{prob:.0f}%"   if isinstance(prob, (int, float)) else "–"

        # UV with Danish bucket label, e.g. "6 (høj)"
        _, uv_label = uv_bucket(uv)
        uv_disp = f"{uv_txt} ({uv_label})" if uv_txt != "–" else "–"

        # Timestamp pretty print "YYYY-MM-DD, HH:MM"
        gen_txt = ""
        if gen:
            try:
                dt = datetime.fromisoformat(gen)
                gen_txt = dt.strftime("%Y-%m-%d, %H:%M")
            except Exception:
                gen_txt = gen  # fallback if parsing fails

        return html.Div(
            [
                # Main row: icon + current temperature (UI text is Danish)
                html.Div(
                    [
                        html.Span(icon, className="wx-ico big"),
                        html.Div([html.Div(now_txt, className="wx-now")], className="wx-now-col"),
                    ],
                    className="wx-row-main",
                ),

                # Details (UI labels in Danish)
                html.Ul(
                    [
                        html.Li([html.Span("Maks T: "),  html.Span(tmax_txt)]),
                        html.Li([
                            html.Span("UV maks: "),
                            html.Span(uv_disp, className=uv_class(uv), title=f"UV {uv_txt}"),
                        ]),
                        html.Li([html.Span("Nedbør: "), html.Span(f"{rain_txt}  {prob_txt}")]),
                    ],
                    className="wx-stats",
                ),

                # Timestamp line
                html.Div(gen_txt, className="wx-ts"),
            ],
            className="box weather-card",
        )
    except Exception as e:
        # Log in English; UI fallback in Danish
        print(f"[weather_box] failed to read {JSON_PATH.resolve()}: {e}")
        return html.Div("Ingen vejrudsigtsdata", className="box weather-card")

# ------------------------------------------------------------
# CLI test
# ------------------------------------------------------------
if __name__ == "__main__":
    print(f"Trying to load weather from: {JSON_PATH.resolve()}")
    box = weather_box()
    print("Children:", box.children)
