#!/usr/bin/env python3
"""Validate the conference data under _data/conferences/.

Checks that every entry has the required fields, that ids are unique, that the
categories exist in _data/types.yml, and that deadlines parse in their declared
timezone. Run it before opening a pull request:

    python3 scripts/validate.py
"""
from __future__ import annotations

import glob
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQUIRED = ("title", "year", "id", "link", "deadline", "timezone", "place", "date", "sub")
FMT = "%Y-%m-%d %H:%M:%S"

# Timezone spellings the site's JavaScript understands (see _includes/utils.js)
# on top of the IANA names that zoneinfo resolves directly.
ALIASES = {"AoE": "Etc/GMT+12", "PST": "Etc/GMT+8", "EST": "Etc/GMT+5", "UTC": "UTC"}
for _o in range(-12, 13):
    ALIASES[f"UTC{'+' if _o >= 0 else '-'}{abs(_o)}"] = f"Etc/GMT{'-' if _o >= 0 else '+'}{abs(_o)}"


def resolve_tz(name: str):
    try:
        return ZoneInfo(ALIASES.get(name, name))
    except (ZoneInfoNotFoundError, ValueError):
        return None


def main() -> int:
    types = yaml.safe_load(open(os.path.join(ROOT, "_data", "types.yml")))
    known_subs = {t["sub"] for t in types}

    errors: list[str] = []
    seen: dict[str, str] = {}
    count = 0

    for path in sorted(glob.glob(os.path.join(ROOT, "_data", "conferences", "*.yml"))):
        rel = os.path.relpath(path, ROOT)
        entries = yaml.safe_load(open(path)) or []
        file_year = int(os.path.splitext(os.path.basename(path))[0])

        for entry in entries:
            count += 1
            label = f"{rel}: {entry.get('id', entry.get('title', '???'))}"

            for field in REQUIRED:
                if not entry.get(field):
                    errors.append(f"{label}: missing required field '{field}'")

            cid = entry.get("id")
            if cid in seen:
                errors.append(f"{label}: duplicate id, already used in {seen[cid]}")
            elif cid:
                seen[cid] = rel

            if entry.get("year") != file_year:
                errors.append(f"{label}: year {entry.get('year')} does not match file {rel}")

            for sub in entry.get("sub") or []:
                if sub not in known_subs:
                    errors.append(f"{label}: unknown category '{sub}' (see _data/types.yml)")

            tz = resolve_tz(entry.get("timezone", ""))
            if tz is None:
                errors.append(f"{label}: unknown timezone '{entry.get('timezone')}'")

            deadlines = {}
            for field in ("abstract_deadline", "deadline"):
                raw = entry.get(field)
                if raw is None or raw == "TBA":
                    continue
                try:
                    deadlines[field] = datetime.strptime(str(raw), FMT)
                except ValueError:
                    errors.append(f"{label}: {field} '{raw}' is not '{FMT}'")

            if len(deadlines) == 2 and deadlines["abstract_deadline"] > deadlines["deadline"]:
                errors.append(f"{label}: abstract_deadline is after deadline")

    for err in errors:
        print(f"ERROR {err}", file=sys.stderr)
    print(f"checked {count} entries in {len(glob.glob(os.path.join(ROOT, '_data', 'conferences', '*.yml')))} files, {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
