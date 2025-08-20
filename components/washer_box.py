# components/washer_box.py
import os
import math
import pandas as pd
from dash import html
from datetime import datetime

CSV_PATH = os.getenv("WASHER_FILE", "data/washer_w.csv")

def washer_box():
    w = float("nan")
    ts_fmt = ""
    try:
        df = pd.read_csv(CSV_PATH, names=["ts", "W"])
        latest = df.iloc[-1]
        w = float(latest["W"])
        ts = str(latest["ts"])
        try:
            dt = datetime.fromisoformat(ts)
            ts_fmt = dt.strftime("%Y-%m-%d, %H:%M")
        except Exception:
            ts_fmt = ts
    except Exception as e:
        print(f"[washer_box] failed to read {CSV_PATH}: {e}")

    text = f"{w:.1f} W" if not math.isnan(w) else "— W"

    # Lägg till "active" om > 0.0
    classes = ["box", "washer-card"]

    force = True  # sätt till 1 för att testa
    if force or (not math.isnan(w) and w > 0.0):
        classes.append("active")

    return html.Div(
        [
            html.Div("Vaskemaskine", className="title"),
            html.Div(text, className="value"),
            html.Div(ts_fmt, className="time"),
        ],
        className=" ".join(classes),
    )
