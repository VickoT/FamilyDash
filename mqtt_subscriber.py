# mqtt_subscriber.py
import os, json, time, threading, copy
from paho.mqtt.client import Client

# ---------- Configuration from environment ----------
MQTT_HOST = os.getenv("MQTT_HOST", "192.168.50.147")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_CLIENT = os.getenv("MQTT_CLIENT", "familydash-default")  # unique per device
MQTT_USER = os.getenv("MQTT_USER", "vicko")
MQTT_PASS = os.getenv("MQTT_PASS", "verysecure123")

SHELLY_PREFIX = os.getenv("SHELLY_PREFIX", "shelly-htg3")     # Shelly sensor prefix
WASHER_PREFIX = os.getenv("WASHER_PREFIX", "home/washer")     # Washer MQTT prefix

# ---------- Shared state ----------
_latest = {
    "shelly": {"tC": None, "rh": None, "ts": None},
    "washer": {"time_to_end": None, "ts": None},
}
_lock = threading.Lock()


# ---------- Public API ----------
def get_snapshot():
    """Return a deep copy of the latest sensor values (thread-safe)."""
    with _lock:
        return copy.deepcopy(_latest)


# ---------- Internal helpers ----------
def _set_shelly(tC=None, rh=None):
    """Update cached Shelly values (temperature / humidity)."""
    if tC is None and rh is None:
        return
    with _lock:
        s = _latest["shelly"]
        if tC is not None:
            s["tC"] = float(tC)
        if rh is not None:
            s["rh"] = float(rh)
        s["ts"] = time.time()


def _set_washer(time_to_end=None):
    """Update cached washer time-to-end (in minutes)."""
    if time_to_end is None:
        return
    with _lock:
        w = _latest["washer"]
        w["time_to_end"] = float(time_to_end)
        w["ts"] = time.time()


# ---------- MQTT callbacks ----------
def _on_connect(cli, _ud, _flags, _rc, _props=None):
    """Subscribe to relevant topics after broker connection."""
    # Shelly sensor topics
    cli.subscribe(f"{SHELLY_PREFIX}/status/#")
    cli.subscribe(f"{SHELLY_PREFIX}/events/#")
    # Washer topic (published by HA automation)
    cli.subscribe(f"{WASHER_PREFIX}/time_to_end")


def _on_message(_cli, _ud, msg):
    """Handle incoming MQTT messages and route them to the right updater."""
    topic = msg.topic
    text = msg.payload.decode("utf-8", "ignore").strip()

    # --- Shelly ---
    try:
        data = json.loads(text)
    except Exception:
        data = None

    if topic.endswith("/status/temperature:0") and isinstance(data, dict):
        t = data.get("tC")
        if isinstance(t, (int, float)):
            _set_shelly(tC=t)
        return

    if topic.endswith("/status/humidity:0") and isinstance(data, dict):
        h = data.get("rh")
        if isinstance(h, (int, float)):
            _set_shelly(rh=h)
        return

    if "/events/" in topic and isinstance(data, dict):
        params = data.get("params") or {}
        t = (params.get("temperature:0") or {}).get("tC")
        h = (params.get("humidity:0") or {}).get("rh")
        if isinstance(t, (int, float)) or isinstance(h, (int, float)):
            _set_shelly(
                tC=t if isinstance(t, (int, float)) else None,
                rh=h if isinstance(h, (int, float)) else None,
            )
        return

    # --- Washer ---
    if topic == f"{WASHER_PREFIX}/time_to_end":
        try:
            _set_washer(time_to_end=float(text))
        except Exception:
            pass


# ---------- Subscriber start ----------
def start():
    """Launch the MQTT client in a background thread (idempotent)."""
    if getattr(start, "_started", False):
        return
    start._started = True

    def _run():
        cli = Client(client_id=MQTT_CLIENT)
        if MQTT_USER:
            cli.username_pw_set(MQTT_USER, MQTT_PASS)
        cli.on_connect = _on_connect
        cli.on_message = _on_message
        cli.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        cli.loop_start()

    threading.Thread(target=_run, name="mqtt-subscriber", daemon=True).start()
