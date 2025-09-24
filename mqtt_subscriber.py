# mqtt_subscriber.py
# -------------------------------------------------------------------------
# FamilyDash MQTT subscriber (fire-and-forget).
#
# Lyssnar på:
#   - Tvättmaskin:  home/washer/time_to_end
#   - Torktumlare:  home/torktumlare/state
#   - Heartbeat:    home/heartbeat
#   - Shelly:       shelly-htg3/#
#
# Håller en tråd-säker snapshot för UI:t:
#   snapshot = {
#     "washer":    {"status": str|None, "time_to_end_min": int|None, "ts": int|None},
#     "dryer":     {"status": str|None, "time_left": int|None,       "ts": int|None},
#     "heartbeat": {"last": str|None,   "ts": int|None},
#     "shelly":    {"tC": float|None,   "rh": float|None, "online": bool|None, "ts": int|None},
#   }
#
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
    # Hantera ev. citattecken i .env ("1883")
    raw = os.getenv("MQTT_PORT", "1883")
    return int(str(raw).strip().strip('"').strip("'"))

MQTT_ENABLE: bool        = os.getenv("MQTT_ENABLE", "1") == "1"
MQTT_HOST: str           = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT: int           = _get_port()
MQTT_USER: Optional[str] = os.getenv("MQTT_USER") or None
MQTT_PASS: Optional[str] = os.getenv("MQTT_PASS") or None
MQTT_CLIENT: str         = os.getenv("MQTT_CLIENT", "familydash-default")

TOPIC_WASHER: str    = "home/washer/time_to_end"
TOPIC_DRYER: str     = "home/torktumlare/state"
SHELLY_PREFIX: str   = "shelly-htg3"
TOPIC_SHELLY: str    = f"{SHELLY_PREFIX}/#"
TOPIC_HEARTBEAT: str = "home/heartbeat"
TOPIC_KIA: str       = "home/kia/state"

DEBUG: bool          = True

# --- Shared snapshot -----------------------------------------------------
_snapshot: Dict[str, Dict[str, Any]] = {
    "washer":    {"status": None, "time_to_end_min": None, "ts": None},
    "dryer":     {"status": None, "time_left": None,       "ts": None},
    "heartbeat": {"last": None,   "ts": None},
    "shelly":    {"tC": None, "rh": None, "online": None,  "ts": None},
    "kia":       {"battery": None, "range": None, "ts": None},
}
_lock = threading.Lock()


def get_snapshot() -> Dict[str, Dict[str, Any]]:
    """Return a deep copy of the latest values (thread-safe)."""
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


def _set(section: str, **kwargs: Any) -> None:
    with _lock:
        _snapshot[section].update({k: v for k, v in kwargs.items() if v is not None})
        _snapshot[section]["ts"] = _now()


# --- MQTT callbacks (Paho v2) -------------------------------------------
def _on_connect(cli: mqtt.Client, _ud: Any, _flags: Any,
                reason_code: mqtt.ReasonCodes, _props: mqtt.Properties | None = None) -> None:
    print(f"[mqtt] connected reason_code={reason_code}, id={MQTT_CLIENT}")
    # Birth (announce online, retained) efter bekräftad uppkoppling
    status_topic = f"clients/{MQTT_CLIENT}/status"
    cli.publish(status_topic, payload="online", qos=1, retain=True)

    # Subscriptions
    cli.subscribe(TOPIC_WASHER, qos=0)
    cli.subscribe(TOPIC_DRYER, qos=0)
    cli.subscribe(TOPIC_HEARTBEAT, qos=0)
    cli.subscribe(TOPIC_SHELLY, qos=0)
    cli.subscribe(TOPIC_KIA, qos=0)
    print(f"[mqtt] subscribed: {TOPIC_WASHER}, {TOPIC_DRYER}, {TOPIC_HEARTBEAT}, {TOPIC_SHELLY}, {TOPIC_KIA}")


def _on_disconnect(cli: mqtt.Client, _ud: Any, reason_code: mqtt.ReasonCodes, _props: mqtt.Properties | None = None) -> None:
    print(f"[mqtt] disconnected reason_code={reason_code}, id={MQTT_CLIENT}")
    # LWT sköter 'offline' vid oväntad disconnect. Vid snygg nedstängning kan man vilja publicera 'offline' här.
    # status_topic = f"clients/{MQTT_CLIENT}/status"
    # cli.publish(status_topic, payload="offline", qos=1, retain=True)


def _parse_shelly(topic: str, payload: str) -> None:
    """
    Shelly Gen3 tolerant parsing:
    - '<prefix>/online' -> 'true'/'false'
    - JSON med nycklar 'tC' och 'rh'
    - Plain numbers på subtopics som .../temperature, .../humidity
    """
    if topic.endswith("/online"):
        _set("shelly", online=(payload.strip().lower() == "true"))
        return

    if payload.startswith("{") and payload.endswith("}"):
        try:
            d = json.loads(payload)
            tC = _to_float(d.get("tC") or d.get("temperature"))
            rh = _to_float(d.get("rh") or d.get("humidity") or d.get("hum"))
            _set("shelly", tC=tC, rh=rh)
            return
        except Exception as e:
            if DEBUG:
                print(f"[mqtt] shelly json warn: {e}")

    low = topic.lower()
    if any(k in low for k in ("/temp", "/temperature")):
        _set("shelly", tC=_to_float(payload))
        return
    if any(k in low for k in ("/hum", "/humidity", "/rh")):
        _set("shelly", rh=_to_float(payload))
        return

def _parse_kia(payload: str) -> None:
    if payload.startswith("{") and payload.endswith("}"):
        try:
            d = json.loads(payload)
            battery = _to_int(d.get("battery"))
            range_km = _to_int(d.get("range"))
            _set("kia", battery=battery, range=range_km)
            return
        except Exception as e:
            if DEBUG:
                print(f"[mqtt] kia json warn: {e}")

def _on_message(_cli: mqtt.Client, _ud: Any, msg: mqtt.MQTTMessage) -> None:
    payload = msg.payload.decode("utf-8", errors="replace").strip()
    if DEBUG:
        print(f"[mqtt] {msg.topic} <- {payload}")

    # Washer --------------------------------------------------------------
    if msg.topic == TOPIC_WASHER:
        status = None
        minutes = None
        if payload.startswith("{") and payload.endswith("}"):
            try:
                data = json.loads(payload)
                status = data.get("status")
                minutes = data.get("time_to_end_min")
            except Exception as e:
                if DEBUG:
                    print(f"[mqtt] washer json warn: {e}")
        else:
            minutes = payload
        _set("washer", status=status, time_to_end_min=_to_int(minutes))
        return

    # Dryer ---------------------------------------------------------------
    if msg.topic == TOPIC_DRYER:
        status = None
        time_left = None
        if payload.startswith("{") and payload.endswith("}"):
            try:
                data = json.loads(payload)
                status = data.get("status")
                time_left = data.get("time_left")
            except Exception as e:
                if DEBUG:
                    print(f"[mqtt] dryer json warn: {e}")
        else:
            time_left = payload
        _set("dryer", status=status, time_left=_to_int(time_left))
        return

    # Heartbeat -----------------------------------------------------------
    if msg.topic == TOPIC_HEARTBEAT:
        _set("heartbeat", last=payload)
        return

    # Shelly --------------------------------------------------------------
    if msg.topic.startswith(SHELLY_PREFIX):
        _parse_shelly(msg.topic, payload)
        return
    # Kia ---------------------------------------------------------------
    if msg.topic == TOPIC_KIA:
        _parse_kia(payload)
        return


# --- Start (idempotent, bakgrundstråd) ----------------------------------
def start() -> None:
    """Start the MQTT client in a background daemon thread (idempotent)."""
    if not MQTT_ENABLE:
        print("[mqtt] disabled (MQTT_ENABLE=0)")
        return
    if getattr(start, "_started", False):
        return
    start._started = True  # type: ignore[attr-defined]

    def _loop() -> None:
        try:
            print(f"[mqtt] host={MQTT_HOST} port={MQTT_PORT} id={MQTT_CLIENT} user={'set' if MQTT_USER else 'none'}")
            cli = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION2,
                client_id=MQTT_CLIENT,
            )
            if MQTT_USER:
                cli.username_pw_set(MQTT_USER, MQTT_PASS)

            # Presence (LWT retained 'offline')
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
