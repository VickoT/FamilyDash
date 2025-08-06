# The Famliy Dashboard

Docker based dashboard application.

**TODO**

* Create a GitHub repo for the project
* Access the Tibber API to get current price and prognosis
* Set up a Docker compose file
* Create graph and view in browser app


Tibber test file works
The Tibber API: [LINK](https://developer.tibber.com/docs/overview)

**The python dotenv**
**MQTT**

- Put in kiosk mode


[Raspberry Pi Touch Display 2](https://www.electrokit.com/raspberry-pi-touch-display-2)
[Pi4](https://www.electrokit.com/raspberry-pi-4-model-b/4gb)

```
Overlay parameters for rotation (via dtoverlay=...rotation=...) are
currently unreliable in Raspberry Pi OS Bookworm, especially with the Touch
Display 2. This is a known issue that will likely be resolved in the future with
improvements to KMS and Weston.
```

Google credentials are stored in the .config folder.

SVELTEKIT?

```
docker compose up --build -d
chromium-browser --kiosk http://localhost:8050
```


## Data Update Strategy

- One script per API (e.g. `fetch_tibber.py`, `fetch_weather.py`, etc.)
  Each script fetches data and stores it under the `data/` directory.
  These scripts are executed via `crontab` on a schedule appropriate to the data source
  (e.g. once per day for Tibber, every 15 minutes for weather, etc).


- In `app.py`, each output component (e.g. a graph or text box) has its own Dash callback
  that reads from the corresponding file in `data/` and updates the component.

- Each callback is triggered by a dedicated `dcc.Interval` component,
  allowing different parts of the dashboard to update at different rates
  (e.g. Tibber prices every hour, Google Calendar every 5 minutes).



WHAT I HAVE DONE:
* create a crontab container to fetch data from APIs
I NEED TO set up callbacks to update the dashboard app
