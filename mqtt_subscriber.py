# mqtt_subscriber.py
import os, json, time, threading, copy
from paho.mqtt.client import Client

MQTT_HOST = os.getenv("MQTT_HOST", "192.168.50.147")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "vicko")
MQTT_PASS = os.getenv("MQTT_PASS", "verysecure123")
SHELLY_PREFIX = os.getenv("SHELLY_PREFIX", "shellyhtg3-e4b323310e10")

_latest = {"shelly": {"tC": None, "rh": None, "ts": None}}
_lock = threading.Lock()

def get_snapshot():
    with _lock:
        return copy.deepcopy(_latest)

def _set_shelly(tC=None, rh=None):
    if tC is None and rh is None: return
    with _lock:
        s = _latest["shelly"]
        if tC is not None: s["tC"] = float(tC)
        if rh is not None: s["rh"] = float(rh)
        s["ts"] = time.time()

def _on_connect(cli, _ud, _flags, _rc, _props=None):
    cli.subscribe(f"{SHELLY_PREFIX}/status/#")
    cli.subscribe(f"{SHELLY_PREFIX}/events/#")

def _on_message(_cli, _ud, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8", "ignore"))
    except Exception:
        return
    topic = msg.topic
    if topic.endswith("/status/temperature:0"):
        t = data.get("tC")
        if isinstance(t, (int, float)): _set_shelly(tC=t)
        return
    if topic.endswith("/status/humidity:0"):
        h = data.get("rh")
        if isinstance(h, (int, float)): _set_shelly(rh=h)
        return
    if "/events/" in topic and isinstance(data, dict):
        params = data.get("params") or {}
        t = (params.get("temperature:0") or {}).get("tC")
        h = (params.get("humidity:0") or {}).get("rh")
        if isinstance(t, (int, float)) or isinstance(h, (int, float)):
            _set_shelly(tC=t if isinstance(t, (int, float)) else None,
                        rh=h if isinstance(h, (int, float)) else None)

def start():
    if getattr(start, "_started", False): return
    start._started = True
    def _run():
        cli = Client(client_id="familydash-shelly")
        if MQTT_USER: cli.username_pw_set(MQTT_USER, MQTT_PASS)
        cli.on_connect = _on_connect
        cli.on_message = _on_message
        cli.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        cli.loop_start()
    threading.Thread(target=_run, name="mqtt-shelly", daemon=True).start()
