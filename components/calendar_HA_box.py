#!/usr/bin/env python3
# compose/print_calendar.py

import time

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from mqtt_subscriber import start, get_snapshot

print("Starting MQTT subscriber ...")
start()

while True:
    snap = get_snapshot()
    cal = snap.get("calendar", {})

    fam = cal.get("familie", {}).get("events_next7d")
    bday = cal.get("fodelsedagar", {}).get("events_next370d")

    print("\n===============================")
    print("Familie kalender:")
    if fam:
        for e in fam[:5]:  # skriv bara de första 5
            summary = e.get("summary")
            start_date = e.get("start", {}).get("date") or e.get("start", {}).get("dateTime")
            print(f"  - {summary} ({start_date})")
    else:
        print("  (ingen data)")

    print("\nFödelsedagar:")
    if bday:
        for e in bday[:5]:
            summary = e.get("summary")
            start_date = e.get("start", {}).get("date") or e.get("start", {}).get("dateTime")
            print(f"  - {summary} ({start_date})")
    else:
        print("  (ingen data)")

    time.sleep(30)
