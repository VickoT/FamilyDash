# Phone Button Feature - TODO

## Goal
Add a button tile to the FamilyDash dashboard that calls Anne's phone using Home Assistant's `script.find_my_phone` when pressed.

## Requirements
- **Button appearance**: Square tile with "Anne" text label above a vibrating phone icon (SVG)
- **Location**: Replace the shelly temperature sensor tile (top row, 4th position)
- **Behavior**:
  - When clicked, trigger HA script `script.find_my_phone`
  - Turn bright green (like washer when active) for 6 seconds
  - Show vibrating animation on phone icon while active
- **Method**: Direct REST API call to Home Assistant (not MQTT)

## Home Assistant Setup ✅
- Script exists: `script.find_my_phone`
- HA URL: `http://192.168.50.147:8123`
- Long-lived access token created (name: "FamilyDash")
- Token added to `.env` file as `HA_TOKEN`

## Implementation Attempted

### Files Created/Modified (all reverted):
1. **`components/phone_button.py`** - Button component with SVG phone icon
2. **`app.py`** - Added imports, callbacks, and button to layout
3. **`assets/style.css`** - Added phone button styles and animations
4. **`docker-compose.override.yml`** - Added HA_URL and HA_TOKEN env vars

### Issues Encountered

1. **SVG Icon Not Rendering**
   - Used `dcc.Markdown(SVG_STRING, dangerously_allow_html=True)` but icon didn't show
   - Tried wrapping in `html.Div` with className but still not visible
   - Issue: SVG might need different approach (e.g., `html.Iframe` with srcdoc, or inline HTML)

2. **Button Not Turning Green**
   - Callback structure looked correct
   - Active state with timestamp tracked in `dcc.Store`
   - Reset after 6 seconds via tick interval
   - Issue: Callback might not have been triggering (no logs appeared)

3. **Environment Variables Not Loading**
   - Added `HA_URL` and `HA_TOKEN` to `.env` file
   - Added them to `docker-compose.override.yml` as `${HA_URL}` and `${HA_TOKEN}`
   - These needed to be passed through to container
   - Container needs restart after adding env vars

## What Worked
- Basic button structure created
- Grid layout updated to replace shelly tile
- CSS styling with green active state and vibration animation
- Callbacks structured correctly for click → API call → visual feedback
- Environment variable configuration in docker-compose

## Next Steps to Try

### Option 1: Fix SVG Rendering
- Try using `html.Iframe(srcDoc=SVG_STRING)` instead of Markdown
- Or use `dangerously_allow_html` in a different Dash component
- Or convert SVG to base64 data URI and use in html.Img

### Option 2: Simplify with Emoji/Unicode
- Use a large phone emoji 📱 instead of SVG
- Much simpler, may be good enough
- Can still do CSS animations on the emoji

### Option 3: Use MQTT Instead of REST API
- Publish MQTT message when button clicked: `home/dashboard/action/ring_anne_phone`
- Create HA automation to listen and trigger script
- No need for HA_TOKEN or HA_URL
- Uses existing MQTT infrastructure
- Requires creating automation in HA

## Files to Keep in Mind
- `.env` - Contains `HA_URL` and `HA_TOKEN` (already set up)
- `docker-compose.override.yml` - Needs env vars passed through
- `app.py` - Main callbacks and layout
- `components/phone_button.py` - Button component
- `assets/style.css` - Styling and animations

## Technical Notes
- Washer active color: `--accent-active: #39ff14` (bright green)
- Active state duration: 6 seconds
- Grid position: `"weather washer climate shelly power"` → replace `shelly` with `phone`
- HA REST API endpoint: `{HA_URL}/api/services/script/find_my_phone`
- Authorization header: `Bearer {HA_TOKEN}`

## Recommendation for Next Session
Start with **Option 2 (emoji)** first as it's the simplest. If that works, can upgrade to SVG later. Focus on getting the functionality working first (button → API call → phone rings), then worry about the icon appearance.
