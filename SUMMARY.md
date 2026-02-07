# Home Assistant Script Trigger Integration

## Overview

Added support for triggering a Home Assistant script directly from the Anne button on FamilyDash via REST. The dashboard now calls `POST /api/services/script/turn_on` with a bearer token whenever the button is pressed and provides user feedback in the tile.

## Key Changes

- Introduced `ha_client.py` to encapsulate REST calls to Home Assistant with timeout handling and error reporting.
- Rebuilt the Anne button component (`components/anne_button.py`) and its styling to show success/error feedback.
- Updated `app.py` callback logic to call Home Assistant, manage transient status state, and log outcomes. Added new `dcc.Store` instances for button state and message TTL.
- Documented the new environment variables (`HA_BASE_URL`, `HA_TOKEN`, `HA_SCRIPT_ANNE`, optional `HA_TIMEOUT`) in `README.md` and `docker-compose.override.yml`.
- Adjusted local Docker Compose override to point `HA_SCRIPT_ANNE` at the actual `script.find_my_phone` entity.

## Environment Configuration

Set the following in `.env` (and any deployment secrets):

```
HA_BASE_URL=http://192.168.50.147:8123
HA_TOKEN=<Home Assistant long-lived token>
HA_SCRIPT_ANNE=script.find_my_phone
HA_TIMEOUT=5  # optional
```

Restart the dashboard container after updating these values. Keep tokens private and regenerate them if they were shared during testing.

## Verification

1. Restart FamilyDash and confirm the container sees the HA variables (`docker compose exec dash env | grep HA_`).
2. Test the REST call manually:

   ```bash
   curl -X POST http://192.168.50.147:8123/api/services/script/turn_on \
        -H "Authorization: Bearer $HA_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"entity_id":"script.find_my_phone"}'
   ```

3. Press the Anne button; it should glow briefly, and Home Assistant should log the script execution.

## Notes

- Errors (missing config, network issues, non-200 responses) are surfaced on the tile and logged as warnings.
- Tokens are sensitive; delete old tokens in Home Assistant once the new one is in use.
