from __future__ import annotations

import logging
import os
from typing import Any, Tuple

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
