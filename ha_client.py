from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Tuple
from zoneinfo import ZoneInfo

import requests

_LOGGER = logging.getLogger(__name__)

_HA_BASE_URL = (os.getenv("HA_BASE_URL") or "").strip().rstrip("/")
_HA_TOKEN = os.getenv("HA_TOKEN")

def _get_timeout() -> float:
    raw = os.getenv("HA_TIMEOUT", "5.0").strip()
    try:
        return float(raw)
    except ValueError:
        _LOGGER.warning("Ogiltigt värde för HA_TIMEOUT: %s", raw)
        return 5.0

_HA_TIMEOUT = _get_timeout()

def call_service(domain: str, service: str, payload: dict[str, Any] | None = None) -> Tuple[bool, str]:
    """Anropa en Home Assistant-tjänst via REST och returnera (lyckades, felmeddelande)."""

    if not _HA_BASE_URL:
        return False, "HA_BASE_URL saknas"
    if not _HA_TOKEN:
        return False, "HA_TOKEN saknas"

    url = f"{_HA_BASE_URL}/api/services/{domain}/{service}"
    headers = {
        "Authorization": f"Bearer {_HA_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=payload or {}, headers=headers, timeout=_HA_TIMEOUT)
    except requests.RequestException as exc:
        _LOGGER.warning("Misslyckad anrop till Home Assistant: %s", exc)
        return False, "Ingen kontakt med Home Assistant"

    if response.status_code in (200, 201):
        return True, ""

    text = (response.text or "").strip()
    _LOGGER.warning("Home Assistant svarade med felkod %s: %s", response.status_code, text)
    return False, "Home Assistant svarade med fel"


def get_energy_today(statistic_ids: list[str]) -> dict[str, float]:
    """Hämta dagens (sedan midnatt) förbrukning per enhet från HA:s statistik.

    Använder HA:s websocket-API (`recorder/statistics_during_period`) eftersom
    långtidsstatistiken inte exponeras via REST. Returnerar {statistic_id: kWh}.
    Vid fel returneras {} (loggas) så anroparen kan visa en placeholder.
    """
    if not _HA_BASE_URL:
        _LOGGER.warning("HA_BASE_URL saknas")
        return {}
    if not _HA_TOKEN:
        _LOGGER.warning("HA_TOKEN saknas")
        return {}
    if not statistic_ids:
        return {}

    try:
        from websocket import create_connection
    except ImportError:
        _LOGGER.warning("websocket-client saknas - kan inte hämta HA-statistik")
        return {}

    ws_url = _HA_BASE_URL.replace("https://", "wss://").replace("http://", "ws://") + "/api/websocket"
    tz = ZoneInfo(os.getenv("LOCAL_TZ", "Europe/Stockholm"))
    midnight = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)

    ws = None
    try:
        ws = create_connection(ws_url, timeout=_HA_TIMEOUT)

        # 1) auth-handskakning
        if json.loads(ws.recv()).get("type") != "auth_required":
            _LOGGER.warning("Oväntat svar från HA websocket (förväntade auth_required)")
            return {}
        ws.send(json.dumps({"type": "auth", "access_token": _HA_TOKEN}))
        if json.loads(ws.recv()).get("type") != "auth_ok":
            _LOGGER.warning("HA websocket-auth misslyckades")
            return {}

        # 2) fråga efter dagens statistik per enhet
        ws.send(json.dumps({
            "id": 1,
            "type": "recorder/statistics_during_period",
            "start_time": midnight.isoformat(),
            "statistic_ids": statistic_ids,
            "period": "day",
            "types": ["change"],
        }))

        result = None
        for _ in range(10):
            msg = json.loads(ws.recv())
            if msg.get("id") == 1 and msg.get("type") == "result":
                result = msg
                break
        if not result or not result.get("success"):
            _LOGGER.warning("statistics_during_period misslyckades: %s", result)
            return {}

        data = result.get("result") or {}
        out: dict[str, float] = {}
        for sid in statistic_ids:
            total = 0.0
            for row in (data.get(sid) or []):
                change = row.get("change")
                if isinstance(change, (int, float)):
                    total += change
            out[sid] = round(total, 2)
        return out
    except Exception as exc:  # noqa: BLE001 - vill aldrig krascha callbacken
        _LOGGER.warning("Misslyckades hämta HA-statistik via websocket: %s", exc)
        return {}
    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:  # noqa: BLE001
                pass
