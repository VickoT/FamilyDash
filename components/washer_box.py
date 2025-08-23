# components/washer_box.py
import os, math, pandas as pd
from dash import html
from datetime import datetime

CSV_PATH = os.getenv("WASHER_FILE", "data/washer_w.csv")

def _read_washer():
    w = float("nan"); ts_fmt = ""
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
    return w, ts_fmt

def washer_render():
    w, ts_fmt = _read_washer()
    text = f"{w:.1f} W" if not math.isnan(w) else "— W"
    active = (not math.isnan(w) and w > 0.0)
    classes = "box washer-card" + (" active" if active else "")
    children = [
        html.Div("Vaskemaskine", className="title"),
        html.Div(text, className="value"),
        html.Div(ts_fmt, className="time"),
    ]
    return children, classes

def washer_box():
    children, classes = washer_render()
    return html.Div(children=children, className=classes, id="washer-box")
