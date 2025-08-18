# components/calendar_box.py
from dash import html
import json, os

CAL_PATH = "data/calendar.json"

def _load_calendar(path=CAL_PATH):
    if not os.path.exists(path):
        return {"generated_at": None, "days": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def calendar_box(path=CAL_PATH):
    data = _load_calendar(path)
    days = data.get("days", [])[:7]
    boxes = []

    for i, day in enumerate(days):
        label = day.get("label", "")
        events = day.get("events", [])

        items = []
        if events:
            events = sorted(events, key=lambda e: (e.get("time") is not None, e.get("time") or ""))
            for e in events:
                t = e.get("time")
                title = e.get("title", "")
                items.append(html.Li(f"{t} - {title}" if t else title))

        boxes.append(
            html.Div(
                className=f"day{' today' if i == 0 else ''}",
                children=[
                    html.Div(label, className="day-title"),
                    html.Ul(items, className="day-content"),
                ],
            )
        )

    return html.Div(id="calendar", className="calendar", children=boxes)


if __name__ == "__main__":
    from dash import Dash
    from pathlib import Path

    # peka upp en nivå: ../assets
    assets = Path(__file__).resolve().parent.parent / "assets"
    app = Dash(__name__, assets_folder=str(assets))

    app.layout = calendar_box()
    app.run(debug=True)
