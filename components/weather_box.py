# components/weather_box.py
# ---------------------------------------------------------------------
# FamilyDash weather card (färgglada ikoner via Meteocons från Iconify)
# Hämtar värden direkt från MQTT-snapshot (mqtt_subscriber.get_snapshot)
# ---------------------------------------------------------------------

import os
from datetime import datetime
from dash import html
from dash_iconify import DashIconify

# Importera snapshot från din subscriber
from mqtt_subscriber import get_snapshot


# --- Ikonmappning: Home Assistant → Meteocons (Iconify) ---------------
ICON_MAP = {
    "sunny":            "meteocons:clear-day",
    "clear-night":      "meteocons:clear-night",
    "partlycloudy":     "meteocons:partly-cloudy-day",
    "cloudy":           "meteocons:cloudy",
    "rainy":            "meteocons:rain",
    "pouring":          "meteocons:heavy-rain",
    "lightning":        "meteocons:thunderstorms",
    "lightning-rainy":  "meteocons:thunderstorms-extreme",
    "snowy":            "meteocons:snow",
    "snowy-rainy":      "meteocons:sleet",
    "hail":             "meteocons:hail",
    "fog":              "meteocons:fog",
    "windy":            "meteocons:wind",
    "windy-variant":    "meteocons:wind",
    "exceptional":      "meteocons:na",
}


# --- UV nivåer (klass och text) ---------------------------------------
def uv_bucket(v):
    if not isinstance(v, (int, float)):
        return "unknown", "–"
    if v <= 2:   return "low",        "Lav"
    if v <= 5:   return "medium",     "Moderat"
    if v <= 7:   return "high",       "Høj"
    if v <= 10:  return "very-high",  "Meget høj"
    return "extreme", "Ekstrem"


def uv_class(v):
    b, _ = uv_bucket(v)
    return f"uv uv-{b}"


# --- Huvudkomponent ----------------------------------------------------
def weather_box():
    try:
        snap = get_snapshot()
        wx = snap.get("weather", {})

        condition   = wx.get("condition") or "cloudy"
        temperature = wx.get("temperature")
        tmax        = wx.get("tmax")
        uvmax       = wx.get("uv_max")
        rain6h      = wx.get("precip_6h")
        prob        = wx.get("precip_prob_max")
        ts          = wx.get("timestamp")

        # Ikonval (flerfärgad Meteocons)
        icon = ICON_MAP.get(condition, "meteocons:cloudy")

        # Formateringar
        now_txt  = f"{temperature:.0f}°C" if isinstance(temperature, (int, float)) else "–°C"
        tmax_txt = f"{tmax:.0f}°C"        if isinstance(tmax, (int, float)) else "–°C"
        uv_txt   = f"{uvmax:.0f}"         if isinstance(uvmax, (int, float)) else "–"
        rain_txt = f"{rain6h:.1f} mm"     if isinstance(rain6h, (int, float)) else "0.0 mm"
        prob_txt = f"{prob:.0f}%"         if isinstance(prob, (int, float)) else "–"

        # UV visning
        _, uv_label = uv_bucket(uvmax)
        uv_disp = f"{uv_txt} ({uv_label})" if uv_txt != "–" else "–"

        # Tidsstämpel (UTC → lokal)
        gen_txt = ""
        if ts:
            try:
                dt = datetime.fromisoformat(ts)
                gen_txt = dt.strftime("%Y-%m-%d, %H:%M")
            except Exception:
                gen_txt = str(ts)

        # --- Bygg HTML -------------------------------------------------
        return html.Div(
            [
                # Översta raden: ikon + temp
                html.Div(
                    [
                        html.Span(DashIconify(icon=icon, width=48), className="wx-ico big"),
                        html.Div([html.Div(now_txt, className="wx-now")], className="wx-now-col"),
                    ],
                    className="wx-row-main",
                ),

                # Prognosdetaljer
                html.Ul(
                    [
                        html.Li([html.Span("Tₘₐₓ: "),  html.Span(tmax_txt)]),
                        html.Li([
                            html.Span("UVₘₐₓ: "),
                            # Tar bort title, kan säker förenkla ovan nu
                            html.Span(uv_disp, className=uv_class(uvmax)),
                        ]),
                        html.Li([html.Span("Nedbør: "), html.Span(f"{rain_txt}  {prob_txt}")]),
                    ],
                    className="wx-stats",
                ),

                # Tidsstämpel
                html.Div(gen_txt, className="wx-ts"),
            ],
            className="box weather-card",
        )

    except Exception as e:
        print(f"[weather_box] failed to read MQTT snapshot: {e}")
        return html.Div("Ingen vejrudsigtsdata", className="box weather-card")


# --- CLI-test ----------------------------------------------------------
if __name__ == "__main__":
    print("Testing weather_box() output…")
    box = weather_box()
    print("Children:", box.children)
