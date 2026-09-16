#!/usr/bin/env python3
"""Regenerate README.md from routes.json.

Run this after adding or changing a route:

    python3 generate_readme.py

Everything between the BEGIN/END markers in README.md is replaced; the
prose above and below the table is preserved and edited by hand.
"""

import json
import os
import re
import sys
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "routes.json")
README = os.path.join(HERE, "README.md")
ROUTES_DIR = "routes"

BEGIN = "<!-- BEGIN ROUTES TABLE -->"
END = "<!-- END ROUTES TABLE -->"


def load():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def check(routes):
    """Warn about data that has drifted from the files on disk."""
    problems = []
    on_disk = {
        f for f in os.listdir(os.path.join(HERE, ROUTES_DIR)) if f.endswith(".gpx")
    }
    listed = {r["file"] for r in routes}

    for missing in sorted(listed - on_disk):
        problems.append(f"in routes.json but no such file: {missing}")
    for orphan in sorted(on_disk - listed):
        problems.append(f"on disk but missing from routes.json: {orphan}")

    return problems


def cell(text):
    """A literal pipe would start a new table column, so escape it."""
    return str(text).replace("|", "\\|")


def row(r):
    link = f"{ROUTES_DIR}/{quote(r['file'])}"
    gpx = f"[GPX]({link})"
    komoot = (
        f"[Komoot](https://www.komoot.com/tour/{r['komoot']})" if r.get("komoot") else "—"
    )
    strava = (
        f"[Strava](https://www.strava.com/routes/{r['strava']})" if r.get("strava") else "—"
    )
    return (
        f"| {r['distance_km']} | +{r['elevation_m']} | {r['ec']:.1f} | "
        f"{cell(r['name'])} | {cell(r['area'])} | {cell(r['surface'])} | "
        f"{gpx} | {komoot} | {strava} |"
    )


def table(routes):
    routes = sorted(routes, key=lambda r: (r["distance_km"], r["elevation_m"]))
    lines = [
        "| km | Ascent | EC | Route | Area | Surface | File | Komoot | Strava |",
        "|---:|-------:|---:|-------|------|---------|------|--------|--------|",
    ]
    lines += [row(r) for r in routes]
    return "\n".join(lines)


def main():
    routes = load()

    problems = check(routes)
    if problems:
        print("Data does not match the files on disk:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    with open(README, encoding="utf-8") as f:
        readme = f.read()

    if BEGIN not in readme or END not in readme:
        print(f"README.md is missing the {BEGIN} / {END} markers.", file=sys.stderr)
        return 1

    new = re.sub(
        re.escape(BEGIN) + r".*?" + re.escape(END),
        f"{BEGIN}\n\n{table(routes)}\n\n{END}",
        readme,
        flags=re.S,
    )

    with open(README, "w", encoding="utf-8") as f:
        f.write(new)

    komoot = sum(1 for r in routes if r.get("komoot"))
    strava = sum(1 for r in routes if r.get("strava"))
    print(f"Wrote {len(routes)} routes ({komoot} on Komoot, {strava} on Strava).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
