# components/automower_box.py
from dash import html, dcc, no_update
from datetime import datetime, timezone
import time

_STALE_SECONDS = 15 * 60  # 15 minutes

SVG_STRING = r"""
<svg class="appliance-svg automower-svg" viewBox="60 0 400 400" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <path fill="currentColor" fill-rule="evenodd" d="M 172 109 L 163 118 L 160 126 L 160 166 L 163 170 L 182 180 L 182 211 L 163 222 L 160 226 L 160 285 L 163 294 L 170 301 L 192 309 L 217 315 L 243 318 L 268 318 L 299 314 L 319 309 L 341 301 L 348 294 L 351 285 L 351 226 L 348 222 L 329 211 L 329 180 L 348 170 L 351 166 L 351 126 L 348 118 L 339 109 L 317 97 L 287 88 L 266 85 L 245 85 L 215 90 L 189 99 Z M 182 128 L 202 117 L 225 109 L 242 106 L 269 106 L 287 109 L 309 117 L 329 128 L 331 131 L 331 156 L 309 167 L 309 223 L 331 235 L 331 281 L 328 285 L 306 292 L 282 297 L 256 299 L 230 297 L 204 292 L 183 285 L 180 281 L 180 235 L 202 223 L 202 167 L 180 156 L 180 131 Z"/>
  <path fill="currentColor" d="M 247 156 L 239 159 L 233 186 L 230 219 L 230 275 L 240 279 L 258 281 L 271 279 L 281 275 L 280 204 L 276 174 L 272 159 L 264 156 Z"/>
</svg>
"""

ACTIVITY_SV = {
    "mowing":     "Klipper",
    "docked":     "Dockad",
    "paused":     "Pausad",
    "error":      "Fel",
    "returning":  "Återvänder",
    "charging":   "Laddar",
    "parked":     "Parkerad",
    "unknown":    "Okänd",
}

def automower_compute(snapshot: dict | None, tz, last_ts: dict | None):
    last_ts = (last_ts or {}).copy()
    m = (snapshot or {}).get("automower") or {}
    ts = m.get("ts")

    if not ts:
        return _placeholder_children(), "box appliance-card automower-card", last_ts

    stale = (time.time() - ts) > _STALE_SECONDS

    if last_ts.get("automower") == ts and last_ts.get("automower_stale") == stale:
        return no_update, no_update, last_ts

    children, klass = _render(m, tz, ts, stale)
    last_ts["automower"] = ts
    last_ts["automower_stale"] = stale
    return children, klass, last_ts

def _placeholder_children():
    return [
        dcc.Markdown(SVG_STRING, dangerously_allow_html=True),
        html.Div("Väntar på data …", className="time"),
    ]

def _render(m: dict, tz, ts: int, stale: bool):
    activity = (m.get("activity") or "").lower()
    battery = m.get("battery")

    activity_label = ACTIVITY_SV.get(activity, activity.capitalize() or "–")

    try:
        battery_str = f"{int(battery)}%"
    except (TypeError, ValueError):
        battery_str = "–"

    if activity == "docked":
        status_mod = "docked"
    elif activity in ("mowing", "returning"):
        status_mod = "mowing"
    else:
        status_mod = "error"

    ts_str = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(tz).strftime("%Y-%m-%d, %H:%M")
    ts_class = "timestamp wx-ts-stale" if stale else "timestamp"

    children = [
        dcc.Markdown(SVG_STRING, dangerously_allow_html=True),
        html.Div(activity_label, className=f"automower-status {status_mod}"),
        html.Div(battery_str, className="value"),
        html.Div(ts_str, className=ts_class),
    ]
    return children, "box appliance-card automower-card"
