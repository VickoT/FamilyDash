# mqtt_subscriber.py
# -------------------------------------------------------------------------
# FamilyDash MQTT subscriber (fire-and-forget).
# Presence (LWT):
#   - LWT (retained):  clients/<client_id>/status = offline
#   - Vid lyckad connect: publish retained "online" på samma topic
# -------------------------------------------------------------------------

from __future__ import annotations

import copy
import json
import os
import threading
import time
from typing import Any, Dict, Optional

import paho.mqtt.client as mqtt

# --- Env -----------------------------------------------------------------
def _get_port() -> int:
    raw = os.getenv("MQTT_PORT", "1883")
    return int(str(raw).strip().strip('"').strip("'"))

MQTT_ENABLE: bool        = os.getenv("MQTT_ENABLE", "1") == "1"
MQTT_HOST: str           = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT: int           = _get_port()
MQTT_USER: Optional[str] = os.getenv("MQTT_USER") or None
MQTT_PASS: Optional[str] = os.getenv("MQTT_PASS") or None
MQTT_CLIENT: str         = os.getenv("MQTT_CLIENT", "familydash-default")

# --- Topics --------------------------------------------------------------
TOPIC_CALENDAR_FAM: str   = "home/calendar/familie/next7d"
TOPIC_CALENDAR_BDAY: str  = "home/calendar/fodelsedagar/next370d"

TOPIC_WASHER: str         = "home/appliance/washer/state"
TOPIC_DRYER: str          = "home/appliance/dryer/state"
TOPIC_HEARTBEAT: str      = "home/system/heartbeat"
TOPIC_CAR: str            = "home/car/state"
TOPIC_SHELLY_BHT: str     = "home/env/livingroom/ht/state"
TOPIC_POWER: str          = "home/tibber/power"

# Air quality (rå JSON från Pico)
TOPIC_AIRQUALITY_RAW: str = "home/env/livingroom/airquality_raw"

SHELLY_PREFIX: str        = "shelly-htg3"
TOPIC_SHELLY: str         = f"{SHELLY_PREFIX}/#"

DEBUG: bool               = True

# --- Shared snapshot -----------------------------------------------------
_snapshot: Dict[str, Dict[str, Any]] = {
    "calendar": {
        "familie":       {"events_next7d": None,   "ts": None},
        "fodelsedagar":  {"events_next370d": None, "ts": None},
    },
    "washer":       {"status": None, "time_to_end_min": None, "ts": None},
    "dryer":        {"status": None, "time_left": None, "ts": None},
    "heartbeat":    {"last": None, "ts": None},
    "shelly":       {"tC": None, "rh": None, "online": None, "ts": None},
    "car":          {"battery": None, "range": None, "ts": None},
    "shelly_bht":   {"t": None, "rh": None, "ts": None},
    "pulse_power":  {"power": None, "ts": None},
    "airquality_raw": {
        "eco2_ppm": None, "tvoc_ppb": None, "aqi": None,
        "temperature_c": None, "pressure_hpa": None, "humidity_pct": None,
        "ts": None
    },
}

_lock = threading.Lock()

def get_snapshot() -> Dict[str, Dict[str, Any]]:
    with _lock:
        return copy.deepcopy(_snapshot)

# --- Helpers -------------------------------------------------------------
def _now() -> int:
    return int(time.time())

def _to_int(v: Any) -> Optional[int]:
    try:
        return int(float(str(v).strip()))
    except Exception:
        return None

def _to_float(v: Any) -> Optional[float]:
    try:
        return float(str(v).strip())
    except Exception:
        return None

def _json_payload(payload: str) -> Optional[dict]:
    if not (payload.startswith("{") and payload.endswith("}")):
        return None
    try:
        return json.loads(payload)
    except Exception:
        return None

def _set(section: str, **kwargs: Any) -> None:
    with _lock:
        _snapshot[section].update({k: v for k, v in kwargs.items() if v is not None})
        _snapshot[section]["ts"] = _now()

# --- Parsers -------------------------------------------------------------
# Parsers for various topics. Each parser extracts relevant fields from the
# payload (which may be JSON or plain text) and updates the shared _snapshot.

def _parse_calendar_fam(payload: str) -> None:
    d = _json_payload(payload)
    if not isinstance(d, dict): return
    events = d.get("events", [])
    with _lock:
        _snapshot["calendar"]["familie"]["events_next7d"] = events
        _snapshot["calendar"]["familie"]["ts"] = _now()

def _parse_calendar_bday(payload: str) -> None:
    d = _json_payload(payload)
    if not isinstance(d, dict): return
    events = d.get("events", [])
    with _lock:
        _snapshot["calendar"]["fodelsedagar"]["events_next370d"] = events
        _snapshot["calendar"]["fodelsedagar"]["ts"] = _now()

def _parse_washer(payload: str) -> None:
    status = None; minutes = None
    d = _json_payload(payload)
    if isinstance(d, dict):
        status = d.get("status")
        minutes = d.get("time_to_end_min")
    else:
        minutes = payload
    _set("washer", status=status, time_to_end_min=_to_int(minutes))

def _parse_dryer(payload: str) -> None:
    status = None; time_left = None
    d = _json_payload(payload)
    if isinstance(d, dict):
        status = d.get("status")
        time_left = d.get("time_left")
    else:
        time_left = payload
    _set("dryer", status=status, time_left=_to_int(time_left))

def _parse_heartbeat(payload: str) -> None:
    _set("heartbeat", last=payload)

def _parse_shelly(topic: str, payload: str) -> None:
    if topic.endswith("/online"):
        _set("shelly", online=(payload.strip().lower() == "true"))
        return
    d = _json_payload(payload)
    if isinstance(d, dict):
        tC = _to_float(d.get("tC") or d.get("temperature"))
        rh = _to_float(d.get("rh") or d.get("humidity") or d.get("hum"))
        _set("shelly", tC=tC, rh=rh)
        return
    low = topic.lower()
    if any(k in low for k in ("/temp", "/temperature")):
        _set("shelly", tC=_to_float(payload)); return
    if any(k in low for k in ("/hum", "/humidity", "/rh")):
        _set("shelly", rh=_to_float(payload)); return

def _parse_car(payload: str) -> None:
    d = _json_payload(payload)
    if not isinstance(d, dict): return
    _set("car",
         battery=_to_int(d.get("battery")),
         range=_to_int(d.get("range")))

def _parse_shelly_bht(payload: str) -> None:
    d = _json_payload(payload)
    if not isinstance(d, dict): return
    _set("shelly_bht",
         t=_to_float(d.get("t")),
         rh=_to_float(d.get("rh")))

def _parse_power(payload: str) -> None:
    d = _json_payload(payload)
    if not isinstance(d, dict): return
    _set("pulse_power", power=_to_float(d.get("power")))

def _parse_airquality_raw(payload: str) -> None:
    d = _json_payload(payload)
    if not isinstance(d, dict): return
    _set("airquality_raw",
         eco2_ppm=_to_int(d.get("eco2_ppm")),
         tvoc_ppb=_to_int(d.get("tvoc_ppb")),
         aqi=_to_int(d.get("aqi")),
         temperature_c=_to_float(d.get("temperature_c")),
         pressure_hpa=_to_float(d.get("pressure_hpa")),
         humidity_pct=_to_float(d.get("humidity_pct")))

# --- MQTT callbacks (Paho v2) -------------------------------------------
def _on_connect(cli: mqtt.Client, _ud: Any, _flags: Any,
                reason_code: mqtt.ReasonCodes, _props: mqtt.Properties | None = None) -> None:
    print(f"[mqtt] connected reason_code={reason_code}, id={MQTT_CLIENT}")
    status_topic = f"clients/{MQTT_CLIENT}/status"
    cli.publish(status_topic, payload="online", qos=1, retain=True)

    cli.subscribe(TOPIC_WASHER, qos=0)
    cli.subscribe(TOPIC_DRYER, qos=0)
    cli.subscribe(TOPIC_HEARTBEAT, qos=0)
    cli.subscribe(TOPIC_SHELLY, qos=0)
    cli.subscribe(TOPIC_CAR, qos=0)
    cli.subscribe(TOPIC_SHELLY_BHT, qos=0)
    cli.subscribe(TOPIC_POWER, qos=0)
    cli.subscribe(TOPIC_AIRQUALITY_RAW, qos=0)
    cli.subscribe(TOPIC_CALENDAR_FAM, qos=1)
    cli.subscribe(TOPIC_CALENDAR_BDAY, qos=1)

    print("[mqtt] subscribed:",
          TOPIC_WASHER, TOPIC_DRYER, TOPIC_HEARTBEAT, TOPIC_SHELLY,
          TOPIC_CAR, TOPIC_SHELLY_BHT, TOPIC_POWER, TOPIC_AIRQUALITY_RAW,
          TOPIC_CALENDAR_FAM, TOPIC_CALENDAR_BDAY)

def _on_disconnect(cli: mqtt.Client, _ud: Any, reason_code: mqtt.ReasonCodes,
                   _props: mqtt.Properties | None = None) -> None:
    print(f"[mqtt] disconnected reason_code={reason_code}, id={MQTT_CLIENT}")

def _on_message(_cli: mqtt.Client, _ud: Any, msg: mqtt.MQTTMessage) -> None:
    payload = msg.payload.decode("utf-8", errors="replace").strip()
    if DEBUG:
        print(f"[mqtt] {msg.topic} <- {payload}")

    if msg.topic == TOPIC_CALENDAR_FAM:     _parse_calendar_fam(payload);  return
    if msg.topic == TOPIC_CALENDAR_BDAY:    _parse_calendar_bday(payload); return
    if msg.topic == TOPIC_WASHER:           _parse_washer(payload);        return
    if msg.topic == TOPIC_DRYER:            _parse_dryer(payload);         return
    if msg.topic == TOPIC_HEARTBEAT:        _parse_heartbeat(payload);     return
    if msg.topic.startswith(SHELLY_PREFIX): _parse_shelly(msg.topic, payload); return
    if msg.topic == TOPIC_CAR:              _parse_car(payload);           return
    if msg.topic == TOPIC_SHELLY_BHT:       _parse_shelly_bht(payload);    return
    if msg.topic == TOPIC_POWER:            _parse_power(payload);         return
    if msg.topic == TOPIC_AIRQUALITY_RAW:   _parse_airquality_raw(payload);return

# --- Start (idempotent, bakgrundstråd) ----------------------------------
def start() -> None:
    if not MQTT_ENABLE:
        print("[mqtt] disabled (MQTT_ENABLE=0)"); return
    if getattr(start, "_started", False):
        return
    start._started = True  # type: ignore[attr-defined]

    def _loop() -> None:
        try:
            print(f"[mqtt] host={MQTT_HOST} port={MQTT_PORT} id={MQTT_CLIENT} user={'set' if MQTT_USER else 'none'}")
            cli = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=MQTT_CLIENT)
            if MQTT_USER:
                cli.username_pw_set(MQTT_USER, MQTT_PASS)

            status_topic = f"clients/{MQTT_CLIENT}/status"
            cli.will_set(status_topic, payload="offline", qos=1, retain=True)

            cli.on_connect = _on_connect
            cli.on_disconnect = _on_disconnect
            cli.on_message = _on_message

            cli.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
            cli.loop_start()
            print("[mqtt] loop started")
        except Exception as e:
            print(f"[mqtt] ERROR: {e}")

    threading.Thread(target=_loop, name="mqtt-loop", daemon=True).start()
