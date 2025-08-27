# mqtt_subscriber.py
import os, json, threading, time
from threading import Lock
from paho.mqtt.client import Client

MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASS = os.getenv("MQTT_PASS")
SHELLY_PREFIX = os.getenv("SHELLY_PREFIX", "shellyhtg3-e4b323310e10")

_latest = {"tC": None, "rh": None, "ts": None}
_lock = Lock()

def get_latest():
    with _lock:
        return dict(_latest)

def _update_from_payload(topic: str, payload: bytes):
    """Uppdatera från status-payload. Tidsstämpel = mottagningstid (alltid)."""
    recv_ts = time.time()
    try:
        data = json.loads(payload.decode("utf-8", "ignore"))
    except Exception:
        return

    updated = {}

    # Temperatur: .../status/temperature:0  -> {"id":0,"tC":22.1,...}
    if topic.endswith("/status/temperature:0") and isinstance(data, dict) and "tC" in data:
        try:
            updated["tC"] = float(data["tC"])
        except Exception:
            pass

    # Fukt: .../status/humidity:0 -> {"id":0,"rh":57.3}
    if topic.endswith("/status/humidity:0") and isinstance(data, dict) and "rh" in data:
        try:
            updated["rh"] = float(data["rh"])
        except Exception:
            pass

    if updated:
        with _lock:
            _latest.update(updated)
            _latest["ts"] = recv_ts  # alltid mottagningstid

def _run():
    cli = Client(client_id="familydash-shelly")
    if MQTT_USER:
        cli.username_pw_set(MQTT_USER, MQTT_PASS)

    def _on_message(_c, _u, msg):
        _update_from_payload(msg.topic, msg.payload)

    cli.on_message = _on_message
    cli.connect(MQTT_HOST, MQTT_PORT, 60)

    # Prenumerera bara på det vi behöver
    cli.subscribe(f"{SHELLY_PREFIX}/status/temperature:0")
    cli.subscribe(f"{SHELLY_PREFIX}/status/humidity:0")

    # Om du vill kunna stödja framtida aggregerade status-meddelanden, ta med:
    # cli.subscribe(f"{SHELLY_PREFIX}/status/#")

    cli.loop_forever(retry_first_connection=True)

_thread = None
def start():
    global _thread
    if _thread and _thread.is_alive():
        return
    _thread = threading.Thread(target=_run, name="mqtt-shelly", daemon=True)
    _thread.start()
