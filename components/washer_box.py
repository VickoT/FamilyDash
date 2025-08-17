# components/washer_box.py
import os, pandas as pd
from dash import html

CSV_PATH = os.getenv("WASHER_FILE", "data/washer_w.csv")

def washer_box():
    try:
        df = pd.read_csv(CSV_PATH, names=["ts", "W"])
        latest = df.iloc[-1]
        w = latest["W"]
        text = f"{w:.1f} W"
    except Exception:
        text = "— W"

    return html.Div(
        [
            html.Div("Vaskemaskine", className="title"),
            html.Div(text, className="value"),
        ],
        className="box"
    )
