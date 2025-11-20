# components/weather_box.py
from datetime import datetime, timezone
from dash import html
from mqtt_subscriber import get_snapshot

ICON_MAP = {
    "sunny": "sunny.svg",
    "clear-night": "clear-night.svg",
    "partlycloudy": "partlycloudy.svg",
    "partlycloudy-night": "partlycloudy-night.svg",
    "cloudy": "cloudy.svg",
    "rainy": "rainy.svg",
    "pouring": "pouring.svg",
    "lightning": "lightning.svg",
    "lightning-rainy": "lightning-rainy.svg",
    "snowy": "snowy.svg",
    "snowy-rainy": "snowy-rainy.svg",
    "hail": "hail.svg",
    "fog": "fog.svg",
    "windy": "windy.svg",
    "windy-variant": "windy-variant.svg",
}

def uv_bucket(v):
    if not isinstance(v, (int, float)): return "unknown", "–"
    if v <= 2:  return "low", "Låg"
    if v <= 5:  return "medium", "Mellan"
    if v <= 7:  return "high", "Hög"
    if v <= 10: return "very-high", "Mycket hög"
    return "extreme", "Extrem"

def uv_class(v):
    b, _ = uv_bucket(v)
    return f"uv uv-{b}"

def icon_src(condition):
    fname = ICON_MAP.get((condition or "").lower(), "cloudy.svg")
    return f"/assets/icons/{fname}"

def weather_box():
    try:
        wx = get_snapshot().get("weather", {})  # vädret ligger på toppnivå

        condition   = wx.get("condition")
        temperature = wx.get("temperature")
        tmax        = wx.get("tmax")
        uvmax       = wx.get("uv_max")
        rain        = wx.get("precipitation")      # <-- rätt fält
        wind_speed  = wx.get("wind_speed")
        ts          = wx.get("ts")

        icon_path = icon_src(condition)

        now_txt  = f"{temperature:.0f}°C" if isinstance(temperature, (int, float)) else "–°C"
        tmax_txt = f"{tmax:.0f}°C"        if isinstance(tmax, (int, float)) else "–°C"
        uv_txt   = f"{uvmax:.1f}"         if isinstance(uvmax, (int, float)) else "–"
        # gör rain till float om det kommer som sträng
        try:
            rain_f = float(rain) if rain is not None else None
        except (TypeError, ValueError):
            rain_f = None
        rain_txt = f"{rain_f:.1f} mm" if isinstance(rain_f, (int, float)) else "– mm"

        # ts: stöd både epoch (sek) och ISO-sträng
        gen_txt = ""
        if ts is not None:
            try:
                if isinstance(ts, (int, float)):
                    dt = datetime.fromtimestamp(float(ts), tz=timezone.utc).astimezone()
                elif isinstance(ts, str):
                    dt = datetime.fromisoformat(ts)
                else:
                    dt = None
                gen_txt = dt.strftime("%Y-%m-%d, %H:%M") if dt else str(ts)
            except Exception:
                gen_txt = str(ts)

        return html.Div(
            [
                html.Div(
                    [
                        html.Img(src=icon_path, className="wx-ico big", draggable="false"),
                        html.Span(now_txt, className="wx-now"),
                    ],
                    className="wx-row-main",
                ),
                html.Ul(
                    [
                        html.Li([html.Span("Tₘₐₓ: "),  html.Span(tmax_txt)]),
                        html.Li([html.Span("UVₘₐₓ: "), html.Span(uv_txt, className=uv_class(uvmax))]),
                        html.Li([html.Span("Nedbør: "),  html.Span(rain_txt)]),
                    ],
                    className="wx-stats",
                ),
                html.Div(gen_txt, className="wx-ts"),
            ],
            className="box weather-card",
        )
    except Exception as e:
        print(f"[weather_box] failed: {e}", flush=True)
        return html.Div("Ingen väderdata", className="box weather-card")
