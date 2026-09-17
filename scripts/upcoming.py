#!/usr/bin/env python3
"""Print upcoming deadlines from _data/conferences/, soonest first.

    python3 scripts/upcoming.py              # everything still open
    python3 scripts/upcoming.py --days 60    # only the next 60 days
    python3 scripts/upcoming.py --sub SYS    # only one category
    python3 scripts/upcoming.py --official   # hide projected (tba) entries
"""
from __future__ import annotations

import argparse
import glob
import os
from datetime import datetime, timezone

import yaml

from validate import resolve_tz  # noqa: E402  (same directory)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=int, help="only deadlines within this many days")
    ap.add_argument("--sub", action="append", help="filter by category (repeatable), e.g. SYS")
    ap.add_argument("--official", action="store_true", help="exclude projected (tba) entries")
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    rows = []
    for path in glob.glob(os.path.join(ROOT, "_data", "conferences", "*.yml")):
        for entry in yaml.safe_load(open(path)) or []:
            if args.official and entry.get("tba"):
                continue
            if args.sub and not set(args.sub) & set(entry.get("sub") or []):
                continue
            raw = entry.get("deadline")
            if raw in (None, "TBA"):
                continue
            tz = resolve_tz(entry.get("timezone", ""))
            if tz is None:
                continue
            when = datetime.strptime(str(raw), "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz)
            days = (when - now).total_seconds() / 86400
            if days < 0 or (args.days is not None and days > args.days):
                continue
            rows.append((days, when, entry))

    for days, when, entry in sorted(rows, key=lambda r: r[0]):
        flag = " (projected)" if entry.get("tba") else ""
        subs = ",".join(entry.get("sub") or [])
        print(
            f"D-{int(days):<4} {entry['title']} {entry['year']:<5} "
            f"{when:%Y-%m-%d %H:%M} {entry['timezone']:<20} [{subs}]{flag}"
        )
    print(f"\n{len(rows)} upcoming deadline(s)")


if __name__ == "__main__":
    main()
