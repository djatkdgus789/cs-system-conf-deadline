#!/usr/bin/env python3
"""Print upcoming deadlines from _data/conferences/, soonest first.

    python3 scripts/upcoming.py              # everything still open
    python3 scripts/upcoming.py --days 60    # only the next 60 days
    python3 scripts/upcoming.py --sub SYS    # only one category
    python3 scripts/upcoming.py --markdown   # the table that goes in README.md
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
    ap.add_argument("--markdown", action="store_true", help="print the README table instead")
    ap.add_argument("--all", action="store_true", help="include deadlines that have already closed")
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    rows = []
    for path in glob.glob(os.path.join(ROOT, "_data", "conferences", "*.yml")):
        for entry in yaml.safe_load(open(path)) or []:
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
            if (days < 0 and not (args.all or args.markdown)):
                continue
            if args.days is not None and days > args.days:
                continue
            rows.append((days, when, entry))

    if args.markdown:
        print_markdown(rows, now)
        return

    for days, when, entry in sorted(rows, key=lambda r: r[0]):
        subs = ",".join(entry.get("sub") or [])
        print(
            f"D-{int(days):<4} {entry['title']} {entry['year']:<5} "
            f"{when:%Y-%m-%d %H:%M} {entry['timezone']:<20} [{subs}]"
        )
    print(f"\n{len(rows)} upcoming deadline(s)")


ORDER = ["SYS", "ARCH", "MLSYS", "HPC", "DB", "NET"]
NAMES = {"SYS": "System", "ARCH": "Architecture", "MLSYS": "ML System",
         "HPC": "HPC", "DB": "Database", "NET": "Network"}


def print_markdown(rows, now):
    """Print the per-category tables that README.md carries."""
    by_cat = {}
    for days, when, entry in rows:
        by_cat.setdefault(entry["sub"][0], []).append((days, when, entry))

    for cat in ORDER:
        group = by_cat.get(cat)
        if not group:
            continue
        print(f"### {NAMES[cat]} (`{cat}`)\n")
        print("| Conference | Abstract | Paper | Timezone | Conference dates | Venue |")
        print("| --- | --- | --- | --- | --- | --- |")
        for days, when, e in sorted(group, key=lambda r: r[1]):
            abstract = str(e.get("abstract_deadline") or "—")[:10]
            paper = str(e["deadline"])[:10]
            if days < 0:
                paper = f"~~{paper}~~"
            name = f"[{e['title']} {e['year']}]({e['link']})"
            print(f"| {name} | {abstract} | {paper} | {e['timezone']} | {e['date']} | {e['place']} |")
        print()


if __name__ == "__main__":
    main()
