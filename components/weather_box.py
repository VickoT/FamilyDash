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

_GREEN_CLASSES = {"lugnt", "nästan lugnt", "lätt bris", "svag vind", "måttlig vind"}
_YELLOW_CLASSES = {"frisk vind", "frisk bris"}

def _wind_class_color(wind_class):
    if not wind_class:
        return "wx-wind-class"
    key = wind_class.lower().strip()
    if key in _GREEN_CLASSES:
        return "wx-wind-class wx-wind-green"
    if key in _YELLOW_CLASSES:
        return "wx-wind-class wx-wind-yellow"
    return "wx-wind-class wx-wind-red"

def weather_box():
    try:
        wx = get_snapshot().get("weather", {})  # vädret ligger på toppnivå

        condition   = wx.get("condition")
        temperature = wx.get("temperature")
        tmax        = wx.get("tmax")
        uvmax       = wx.get("uv_max")
        rain        = wx.get("precipitation")      # <-- rätt fält
        wind_speed  = wx.get("wind_speed")
        wind_gust   = wx.get("wind_gust")
        wind_dir    = wx.get("wind_dir")
        wind_class  = wx.get("wind_class")
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

        if isinstance(wind_speed, (int, float)):
            gust_txt  = f" ({wind_gust:.0f})" if isinstance(wind_gust, (int, float)) else ""
            dir_txt   = f"{wind_dir} " if wind_dir else ""
            wind_metrics = f"{dir_txt}{wind_speed:.0f} m/s{gust_txt}"
        else:
            wind_metrics = "–"
        wind_class_color = _wind_class_color(wind_class)

        # ts: stöd både epoch (sek) och ISO-sträng
        gen_txt = ""
        ts_stale = False
        if ts is not None:
            try:
                if isinstance(ts, (int, float)):
                    dt = datetime.fromtimestamp(float(ts), tz=timezone.utc).astimezone()
                elif isinstance(ts, str):
                    dt = datetime.fromisoformat(ts)
                else:
                    dt = None
                gen_txt = dt.strftime("%Y-%m-%d, %H:%M") if dt else str(ts)
                if dt:
                    age = datetime.now(tz=timezone.utc) - dt.astimezone(timezone.utc)
                    ts_stale = age.total_seconds() > 6 * 3600
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
                html.Div([
                    html.Span(wind_metrics, className="wx-wind-metrics"),
                    html.Span(wind_class or "", className=wind_class_color),
                ], className="wx-wind"),
                html.Ul(
                    [
                        html.Li([html.Span("Tₘₐₓ: "),  html.Span(tmax_txt)]),
                        html.Li([html.Span("UVₘₐₓ: "), html.Span(uv_txt, className=uv_class(uvmax))]),
                        html.Li([html.Span("Nedbør: "),  html.Span(rain_txt)]),
                    ],
                    className="wx-stats",
                ),
                html.Div(gen_txt, className="wx-ts wx-ts-stale" if ts_stale else "wx-ts"),
            ],
            className="box weather-card",
        )
    except Exception as e:
        print(f"[weather_box] failed: {e}", flush=True)
        return html.Div("Ingen väderdata", className="box weather-card")
