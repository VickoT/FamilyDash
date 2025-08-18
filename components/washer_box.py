# components/washer_box.py
import os
import pandas as pd
from dash import html
from datetime import datetime

CSV_PATH = os.getenv("WASHER_FILE", "data/washer_w.csv")

def washer_box():
    try:
        df = pd.read_csv(CSV_PATH, names=["ts", "W"])
        latest = df.iloc[-1]
        w = latest["W"]
        ts = latest["ts"]

        # försök tolka ISO-format och formatera om
        try:
            dt = datetime.fromisoformat(str(ts))
            ts_fmt = dt.strftime("%Y-%m-%d, %H:%M")
        except Exception:
            ts_fmt = str(ts)  # fallback om konstigt format

        text = f"{w:.1f} W"
    except Exception:
        text = "— W"
        ts_fmt = ""

    return html.Div(
        [
            html.Div("Vaskemaskine", className="title"),
            html.Div(text, className="value"),
            html.Div(ts_fmt, className="time"),
        ],
        className="box washer-card"
    )
