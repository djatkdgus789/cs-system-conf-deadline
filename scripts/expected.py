#!/usr/bin/env python3
"""Regenerate _data/expected.yml: estimated deadlines for watched conferences.

Every conference on the watchlist has no published CFP for its next edition.
For each, this takes the deadlines of its most recent edition that has fully
closed and moves them forward one year. The result is an estimate, shown on the
site with "(Expected)" next to the countdown and kept apart from
_data/conferences/, which only ever holds dates from a published CFP.

Previous editions' dates come from the ccfddl/ccf-deadlines dataset, or from
MANUAL below for series the dataset does not track. When a conference's real
CFP comes out, add its entry to _data/conferences/ and drop it from the
watchlist; the next run of this script then stops estimating it.

Usage:
    python3 scripts/expected.py                 # clones the dataset itself
    python3 scripts/expected.py --dataset DIR   # reuse an existing clone
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys
import tempfile
from datetime import datetime, timezone

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_updates import clone_dataset  # noqa: E402
from validate import resolve_tz  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FMT = "%Y-%m-%d %H:%M:%S"
DATASET_URL = "https://github.com/ccfddl/ccf-deadlines"

# Previous editions' ORIGINAL deadlines, checked against the official call
# (2026-10-28). These win over the dataset, which often records an extended
# deadline instead of the original - an estimate built on an extension runs
# late. Also covers series the dataset does not track. "source" says where the
# date was read; AoE is assumed where the call gave no timezone (noted).
MANUAL = {
    # Not in the dataset.
    "CASES": {"year": 2026, "timezone": "AoE",
              "rounds": [{"deadline": "2026-03-30 23:59:59"}],
              "source": "ESWEEK 2026 journal-track deadline (shared by EMSOFT, CASES and CODES+ISSS)"},
    "ICPE": {"year": 2026, "timezone": "AoE",
             "rounds": [{"abstract_deadline": "2025-11-03 23:59:59", "deadline": "2025-11-10 23:59:59"}],
             "source": "ICPE 2026 research-track important dates (before its extension)"},
    "DIMES": {"year": 2026, "timezone": "AoE",
              "rounds": [{"deadline": "2026-05-29 23:59:59"}],
              "source": "DIMES'26 call for papers on hpc-announce (before its extension)"},
    "EuroMLSys": {"year": 2026, "timezone": "AoE",
                  "rounds": [{"deadline": "2026-02-15 23:59:59"}],
                  "source": "EuroMLSys 2026 call, site source euromlsys/euromlsys.github.io (before its extension to 02-24)"},
    "CHEOPS": {"year": 2026, "timezone": "AoE",
               "rounds": [{"abstract_deadline": "2026-01-26 23:59:59", "deadline": "2026-02-02 23:59:59"}],
               "source": "CHEOPS 2026 call, site source cheops-workshop/cheops-workshop.github.io (before its extension; no timezone given, AoE assumed)"},
    "MASCOTS": {"year": 2026, "timezone": "AoE",
                "rounds": [{"deadline": "2026-05-17 23:59:59"}],
                "source": "MASCOTS 2026 deadline as listed by an aggregator (official page not reachable)"},
    "NVMSA": {"year": 2026, "timezone": "AoE",
              "rounds": [{"deadline": "2026-04-20 23:59:59"}],
              "source": "NVMSA 2026 deadline as listed by an aggregator (official page not reachable; no timezone)"},
    # In the dataset, but recorded there as an extended deadline (or wrong zone).
    "ICDCS": {"year": 2026, "timezone": "AoE",
              "rounds": [{"abstract_deadline": "2025-12-05 23:59:59", "deadline": "2025-12-12 23:59:59"}],
              "source": "ICDCS 2026 call as originally posted (extended on 2025-11-23 to 01-21; no timezone seen, AoE assumed)"},
    "GPGPU": {"year": 2026, "timezone": "AoE",
              "rounds": [{"deadline": "2026-01-14 23:59:59"}],
              "source": "GPGPU 2026 call (with ASPLOS '26), before its extension"},
    "CF": {"year": 2026, "timezone": "AoE",
           "rounds": [{"abstract_deadline": "2026-01-12 23:59:59", "deadline": "2026-01-19 23:59:59"}],
           "source": "Computing Frontiers 2026 call on hpc-announce, before two extensions"},
    "ISLPED": {"year": 2026, "timezone": "America/Los_Angeles",
               "rounds": [{"abstract_deadline": "2026-03-02 23:59:00", "deadline": "2026-03-09 23:59:00"}],
               "source": "ISLPED 2026 call for papers (11:59 pm Pacific)"},
    "Euro-Par": {"year": 2026, "timezone": "AoE",
                 "rounds": [{"abstract_deadline": "2026-02-27 23:59:59", "deadline": "2026-03-06 23:59:59"}],
                 "source": "Euro-Par 2026 call for papers, before its extension"},
    "CLOUD": {"year": 2026, "timezone": "AoE",
              "rounds": [{"deadline": "2026-03-08 23:59:59"}],
              "source": "IEEE CLOUD 2026 call, before its extension (no timezone given, AoE assumed)"},
    "PACT": {"year": 2026, "timezone": "AoE",
             "rounds": [{"abstract_deadline": "2026-04-17 23:59:59", "deadline": "2026-04-24 23:59:59"}],
             "source": "PACT 2026 call for papers, before its extension"},
    "CLUSTER": {"year": 2026, "timezone": "AoE",
                "rounds": [{"abstract_deadline": "2026-04-23 23:59:59", "deadline": "2026-04-30 23:59:59"}],
                "source": "IEEE CLUSTER 2026 site source, original (struck-through) dates"},
    "SYSTOR": {"year": 2026, "timezone": "AoE",
               "rounds": [{"deadline": "2026-05-21 23:59:59"}],
               "source": "SYSTOR 2026 call on hpc-announce, before its extension"},
    "RTSS": {"year": 2026, "timezone": "AoE",
             "rounds": [{"abstract_deadline": "2026-05-21 23:59:59", "deadline": "2026-05-26 23:59:59"}],
             "source": "RTSS 2026 call for papers (abstract and paper split on 2026-04-10)"},
    "HotStorage": {"year": 2026, "timezone": "AoE",
                   "rounds": [{"deadline": "2026-06-05 23:59:59"}],
                   "source": "HotStorage 2026 call for papers, before its extension"},
}

HEADER = """---

# GENERATED by scripts/expected.py - do not edit by hand; edit the script's
# MANUAL table or the watchlist and re-run it.
#
# ESTIMATES, not deadlines. None of these conferences has published a call for
# papers for the edition listed. Each date is the previous edition's deadline
# moved forward one year, and is shown on the site with "(Expected)" after the
# countdown. Real CFP dates go in _data/conferences/ instead.
#
# Generated {generated} from {source}.
"""


def parse(raw) -> datetime | None:
    try:
        return datetime.strptime(str(raw), FMT)
    except ValueError:
        return None


def add_years(when: datetime, n: int) -> datetime:
    try:
        return when.replace(year=when.year + n)
    except ValueError:  # 29 February
        return when.replace(year=when.year + n, day=28)


def dataset_editions(dataset_dir: str) -> dict:
    out = {}
    for path in glob.glob(os.path.join(dataset_dir, "conference", "*", "*.yml")):
        docs = yaml.safe_load(open(path)) or []
        if docs:
            out[os.path.splitext(os.path.basename(path))[0]] = docs[0]
    return out


def last_closed_edition(series: dict, now: datetime) -> dict | None:
    """The most recent edition whose deadlines are all known and all past."""
    for conf in sorted(series.get("confs") or [], key=lambda c: c["year"], reverse=True):
        rounds = []
        for item in conf.get("timeline") or []:
            dl = parse(item.get("deadline"))
            if dl is None:
                rounds = []
                break
            tz = resolve_tz(conf.get("timezone", "AoE"))
            if tz is None or dl.replace(tzinfo=tz) > now:
                rounds = []
                break
            rounds.append(item)
        if rounds:
            return {"year": conf["year"], "timezone": conf.get("timezone", "AoE"),
                    "rounds": rounds, "source": f"ccf-deadlines ({conf.get('link', '')})"}
    return None


SEASONS = {"Spring", "Summer", "Fall", "Autumn", "Winter"}
MONTHS = {"January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"}
ORDINALS = {"First": "first", "Second": "second", "Third": "third"}


# Round names for series whose dataset entries carry no usable comment, matching
# the names their real entries use in _data/conferences/.
ROUND_NAMES = {
    "NSDI": ["Spring", "Fall"],
    "EDBT": ["Cycle 1", "Cycle 2", "Cycle 3"],
    "IMC": ["Cycle 1", "Cycle 2"],
}


def round_label(name: str, item: dict, index: int, total: int) -> str:
    """' (Spring)', ' (April cycle)', ' (first round)' or ' (round 2)'."""
    if total == 1:
        return ""
    names = ROUND_NAMES.get(name)
    if names and len(names) == total:
        return f" ({names[index]})"
    for word in re.findall(r"[A-Z][a-z]+", item.get("comment") or ""):
        if word in SEASONS:
            return f" ({word})"
        if word in MONTHS:
            return f" ({word} cycle)"
        if word in ORDINALS:
            return f" ({ORDINALS[word]} round)"
    return f" (round {index + 1})"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dataset", help="existing ccf-deadlines clone")
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    tmp = None
    dataset = args.dataset
    if not dataset:
        tmp = tempfile.TemporaryDirectory()
        dataset = clone_dataset(os.path.join(tmp.name, "ccf"))
    editions = dataset_editions(dataset)
    watchlist = yaml.safe_load(open(os.path.join(ROOT, "_data", "watchlist.yml"))) or []

    entries, skipped = [], []
    for w in watchlist:
        name = w["name"]
        base = MANUAL.get(name)
        if base is None and w.get("ccfddl") in editions:
            base = last_closed_edition(editions[w["ccfddl"]], now)
        if base is None:
            skipped.append(f"{name}: no previous deadline on record")
            continue
        if base["year"] < now.year - 1:
            skipped.append(f"{name}: last edition on record is {base['year']}")
            continue
        tz = resolve_tz(base["timezone"])
        year = base["year"] + 1
        total = len(base["rounds"])
        for i, item in enumerate(sorted(base["rounds"], key=lambda r: str(r["deadline"]))):
            old = parse(item["deadline"])
            new = add_years(old, 1)
            if new.replace(tzinfo=tz) <= now:
                continue  # the estimate is already in the past: nothing to count down to
            label = round_label(name, item, i, total)
            entry = {
                "title": f"{name}{label}",
                "year": year,
                "id": re.sub(r"[^a-z0-9]", "", name.lower()) + f"{year % 100}" + (f"r{i + 1}" if total > 1 else "") + "x",
                "expected": True,
                "link": w["cfp"],
            }
            abstract = parse(item.get("abstract_deadline"))
            if abstract:
                entry["abstract_deadline"] = add_years(abstract, 1).strftime(FMT)
            entry["deadline"] = new.strftime(FMT)
            entry["timezone"] = base["timezone"]
            entry["sub"] = w["sub"]
            entry["based_on"] = f"{name} {base['year']}: {old.strftime(FMT)} ({base['timezone']})"
            entry["based_on_source"] = base["source"]
            entries.append(entry)

    entries.sort(key=lambda e: e["deadline"])
    body = yaml.safe_dump(entries, sort_keys=False, allow_unicode=True, width=100)
    path = os.path.join(ROOT, "_data", "expected.yml")
    with open(path, "w") as f:
        f.write(HEADER.format(generated=now.strftime("%Y-%m-%d"),
                              source="ccfddl/ccf-deadlines and the MANUAL table") + "\n" + body)
    print(f"wrote {len(entries)} expected deadline(s) to {os.path.relpath(path, ROOT)}")
    for s in skipped:
        print(f"  skipped {s}")
    if tmp:
        tmp.cleanup()
    return 0


if __name__ == "__main__":
    sys.exit(main())
