# components/weather_box.py
import os, json
from pathlib import Path
from dash import html

# altid finde .../data/weather.json relativt projektet
BASE_DIR = Path(__file__).resolve().parents[1]
JSON_PATH = Path(os.getenv("WEATHER_FILE", str(BASE_DIR / "data" / "weather.json")))

def weather_box():
    try:
        with open(JSON_PATH, encoding="utf-8") as f:
            data = json.load(f)

        cur   = data.get("current", {})
        today = data.get("today", {})

        icon = today.get("icon") or cur.get("icon") or "🌡️"
        tmax = today.get("t_max")
        uv   = today.get("uv_max")
        rain = today.get("precip_sum_mm")
        prob = today.get("precip_prob_max")

        tmax_txt = f"{tmax:.0f}°C" if isinstance(tmax,(int,float)) else "–°C"
        uv_txt   = f"UV {uv:.0f}"   if isinstance(uv,(int,float))   else "UV –"
        rain_txt = f"{rain:.1f} mm" if isinstance(rain,(int,float)) else "0 mm"
        prob_txt = f"{prob:.0f}%"   if isinstance(prob,(int,float)) else "–"

        return html.Div(
            [
                html.Div("Vejr", className="wx-title"),
                html.Div([html.Span(icon, className="wx-ico"),
                          html.Span(tmax_txt, className="wx-temp")], className="wx-row"),
                html.Div([html.Span(uv_txt), html.Span(rain_txt), html.Span(prob_txt)], className="wx-meta"),
            ],
            className="box weather-card"
        )
    except Exception as e:
        print(f"[weather_box] kunne ikke indlæse {JSON_PATH.resolve()}: {e}")
        return html.Div("Ingen vejrinformation", className="box weather-card")


# ------------------------------------------------------------
# Test fra terminalen
# ------------------------------------------------------------
if __name__ == "__main__":
    print(f"Prøver at indlæse vejr fra: {JSON_PATH.resolve()}")
    box = weather_box()
    print("Children:", box.children)
