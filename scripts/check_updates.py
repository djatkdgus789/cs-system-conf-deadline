#!/usr/bin/env python3
"""Report deadlines that may need attention, for the weekly check.

The script does NOT edit the data. Every entry in _data/conferences/ is meant to
come from a conference's own call for papers, and community datasets are
routinely a day off — four entries in this repository had to be corrected
against the official pages after being taken from one. So this only produces a
list of things to go and confirm by hand.

It reports three kinds of finding:

  NEW       a conference on the watchlist now has an upcoming deadline in the
            community dataset, so its CFP may be out — go read `cfp` and add it
  CHANGED   an entry here and the dataset disagree about a date
  EXPIRED   a deadline here has passed, so the next round may be worth adding

Usage:
    python3 scripts/check_updates.py                    # clones the dataset itself
    python3 scripts/check_updates.py --dataset DIR      # reuse an existing clone
    python3 scripts/check_updates.py --format markdown  # for the weekly issue
"""
from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
import tempfile
from datetime import date, datetime

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_URL = "https://github.com/ccfddl/ccf-deadlines.git"


def load_ours() -> list[dict]:
    out = []
    for path in glob.glob(os.path.join(ROOT, "_data", "conferences", "*.yml")):
        out += yaml.safe_load(open(path)) or []
    return out


def clone_dataset(dest: str) -> str:
    subprocess.run(
        ["git", "clone", "--depth", "1", "--quiet", DATASET_URL, dest],
        check=True,
    )
    return dest


def dataset_deadlines(dataset_dir: str, today: date) -> dict[str, list[dict]]:
    """Upcoming deadlines per conference file basename, e.g. {"osdi": [...]}"""
    found: dict[str, list[dict]] = {}
    pattern = os.path.join(dataset_dir, "conference", "*", "*.yml")
    for path in glob.glob(pattern):
        base = os.path.splitext(os.path.basename(path))[0]
        try:
            docs = yaml.safe_load(open(path))
        except yaml.YAMLError:
            continue
        if not docs:
            continue
        doc = docs[0]
        for conf in doc.get("confs") or []:
            for slot in conf.get("timeline") or []:
                raw = slot.get("deadline")
                if not raw or str(raw) in ("TBA", "TBD"):
                    continue
                try:
                    when = datetime.strptime(str(raw)[:10], "%Y-%m-%d").date()
                except ValueError:
                    continue
                if when < today:
                    continue
                found.setdefault(base, []).append(
                    {
                        "date": when,
                        "deadline": str(raw),
                        "abstract": str(slot.get("abstract_deadline") or ""),
                        "year": conf.get("year"),
                        "comment": slot.get("comment") or "",
                        "link": conf.get("link") or "",
                    }
                )
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", help="path to an existing ccf-deadlines clone")
    ap.add_argument("--format", choices=["text", "markdown"], default="text")
    args = ap.parse_args()

    today = date.today()
    ours = load_ours()
    watchlist = yaml.safe_load(open(os.path.join(ROOT, "_data", "watchlist.yml"))) or []

    tmp = None
    dataset_dir = args.dataset
    if not dataset_dir:
        tmp = tempfile.mkdtemp(prefix="ccfddl-")
        dataset_dir = clone_dataset(os.path.join(tmp, "ccf-deadlines"))
    upstream = dataset_deadlines(dataset_dir, today)

    findings: list[tuple[str, str, str]] = []

    def series_of(entry: dict) -> str | None:
        """The dataset file basename covering this entry, if any."""
        for key in upstream:
            if entry["id"].startswith(key):
                return key
        return None

    # NEW: a watched conference now has an upcoming deadline upstream.
    for watched in watchlist:
        key = watched.get("ccfddl")
        if not key or key not in upstream:
            continue
        for slot in sorted(upstream[key], key=lambda s: s["date"]):
            findings.append((
                "NEW",
                f"{watched['name']} {slot['year']}",
                f"dataset lists {slot['deadline']}"
                + (f" ({slot['comment']})" if slot["comment"] else "")
                + f" - confirm at {watched['cfp']}",
            ))

    # EXPIRED: a deadline has passed and no other round of the same series is open.
    open_series = {
        series_of(e)
        for e in ours
        if str(e.get("deadline")) != "TBA"
        and datetime.strptime(str(e["deadline"]), "%Y-%m-%d %H:%M:%S").date() >= today
    }
    for entry in ours:
        raw = str(entry.get("deadline"))
        if raw == "TBA":
            continue
        when = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S").date()
        if when >= today:
            continue
        if series_of(entry) in open_series:
            continue  # another round of this conference is still open
        findings.append((
            "EXPIRED",
            f"{entry['title']} {entry['year']}",
            f"closed {when} - the next round may be worth adding ({entry['link']})",
        ))

    # CHANGED: our date and the dataset's differ for what is clearly the same round.
    # Each entry is matched to its NEAREST upstream deadline in the same series and
    # year; anything more than a fortnight away is a different round, not a change.
    for entry in ours:
        raw = str(entry.get("deadline"))
        if raw == "TBA":
            continue
        when = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S").date()
        if when < today:
            continue
        key = series_of(entry)
        if not key:
            continue
        same_year = [s for s in upstream[key] if s["year"] == entry["year"]]
        if not same_year:
            continue
        nearest = min(same_year, key=lambda s: abs((s["date"] - when).days))
        gap = abs((nearest["date"] - when).days)
        if 0 < gap <= 14:
            findings.append((
                "CHANGED",
                f"{entry['title']} {entry['year']}",
                f"here {when}, dataset {nearest['date']}"
                + (f" ({nearest['comment']})" if nearest["comment"] else "")
                + f" - confirm at {entry['link']}",
            ))

    seen = set()
    unique = []
    for f in findings:
        if f not in seen:
            seen.add(f)
            unique.append(f)

    if args.format == "markdown":
        if not unique:
            print("Nothing to confirm this week.")
        else:
            print(f"Checked {len(ours)} entries and {len(watchlist)} watched conferences on {today}.\n")
            print("Each line is a **candidate**, not a correction — confirm it against the")
            print("conference's own CFP page before editing `_data/conferences/`.\n")
            for kind in ("NEW", "CHANGED", "EXPIRED"):
                rows = [f for f in unique if f[0] == kind]
                if not rows:
                    continue
                print(f"### {kind} ({len(rows)})\n")
                for _, name, detail in rows:
                    print(f"- **{name}** — {detail}")
                print()
    else:
        for kind, name, detail in unique:
            print(f"{kind:<8} {name:<34} {detail}")
        print(f"\n{len(unique)} finding(s) from {len(ours)} entries and {len(watchlist)} watched conferences")

    return 0


if __name__ == "__main__":
    sys.exit(main())
