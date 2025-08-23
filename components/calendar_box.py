from dash import html
import json, os, re

CAL_PATH = "data/calendar.json"

def _load_calendar(path=CAL_PATH):
    if not os.path.exists(path):
        return {"generated_at": None, "days": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def _is_sunday(label: str) -> bool:
    # Stöder da/sv/en, case-insensitive. T.ex. "Søn 24/Aug", "Sön …", "Sun …"
    lab = (label or "").strip().lower()
    return lab.startswith(("søn", "sön", "sun"))

def calendar_box(path=CAL_PATH):
    data = _load_calendar(path)
    days = data.get("days", [])[:7]
    boxes = []

    for i, day in enumerate(days):
        label = day.get("label", "")
        events = day.get("events", [])

        # Märk söndag
        title_cls = "day-label sunday" if _is_sunday(label) else "day-label"

        # Sortera events: None sist
        items = []
        if events:
            events = sorted(events, key=lambda e: (e.get("time") is None, e.get("time") or ""))
            for e in events:
                t = e.get("time")
                title = e.get("title", "")
                items.append(html.Li(f"{t} - {title}" if t else title))

        boxes.append(
            html.Div(
                className=f"day{' today' if i == 0 else ''}",
                children=[
                    html.Div(label, className=title_cls),
                    html.Ul(items, className="events"),
                ],
            )
        )

    return boxes
