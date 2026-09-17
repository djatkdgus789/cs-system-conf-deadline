# CS System Conference Deadlines

Countdowns to computer **systems**, **architecture**, **ML systems**, **HPC**, **database** and
**networking** conference deadlines.

Built on [ai-deadlines](https://github.com/abhshkdz/ai-deadlines) by
[abhshkdz](https://github.com/abhshkdz), via the
[KAIST CASYS fork](https://github.com/casys-kaist/casys-kaist.github.io). The site machinery is
the same; the conference list is the part that is specific to this repository.

## Only published CFPs

**Every deadline here comes from a conference's own call-for-papers or important-dates page.**
Nothing is extrapolated from a previous edition — if a conference has not released its CFP, it is
simply absent until it does. So the list is short by design: it answers "where can I actually
submit right now", not "what might the calendar look like next year".

Deadlines still move after a CFP is published. The `link` on every entry points at the page the
date came from — check it before you rely on one.

## What's covered

25 deadlines as of September 2026, all for 2027 editions:

| Category | Tag | Conferences |
| --- | --- | --- |
| System | `SYS` | OSDI, EuroSys (Fall), NSDI (Fall), SIGMETRICS (Fall, Winter), DSN, RTAS, MMSys |
| Architecture | `ARCH` | DATE, DAC, FPGA |
| ML System | `MLSYS` | MLSys |
| HPC | `HPC` | IPDPS, CCGrid |
| Database | `DB` | SIGMOD (R4), PODS (C2), VLDB (6 monthly rounds), ICDE (R2), EDBT (C3) |
| Network | `NET` | NSDI, MMSys |

Conferences tracked but currently absent because their 2027/2028 CFP is not out: SOSP, SIGOPS ATC,
FAST, SoCC, Middleware, APSys, HotOS, ICDCS, CLOUD, MASCOTS, SYSTOR, VEE, SenSys, ISCA, MICRO,
ASPLOS, HPCA, PACT, ICS, ISPASS, IISWC, SC, PPoPP, HPDC, ICPP, CLUSTER, Euro-Par, EuroMLSys,
SIGCOMM, CoNEXT, HotNets, IMC, BigData, DASFAA. Add them when their CFP appears.

> Note: USENIX ATC ended with the 2025 edition; ACM SIGOPS now runs it as **SIGOPS ATC**.

## Adding or updating a conference

1. Confirm the date on the conference's own CFP page. Third-party deadline aggregators are often
   off by a day — several entries here had to be corrected against the official pages.
2. Edit the file under `_data/conferences/` named after the **conference year**, not the submission
   year (`2027.yml` holds a deadline in December 2026 for a conference held in July 2027).
3. One entry per deadline. A conference with several rounds gets several entries
   (`EuroSys (Fall)`, `SIGMOD (Round 4)`, …), each with its own unique `id`.

```yaml
- title: OSDI                              # short name shown in the list
  year: 2027                               # conference year
  id: osdi27                               # unique, lower case; used in URLs and CSS ids
  full_name: USENIX Symposium on Operating Systems Design and Implementation
  link: https://www.usenix.org/conference/osdi27/call-for-papers   # the page the date came from
  abstract_deadline: "2026-12-01 17:59:59" # omit when the CFP has no abstract deadline
  deadline: "2026-12-08 17:59:59"
  timezone: America/New_York               # AoE, UTC, UTC-4, PST, or an IANA name
  place: Baltimore, MD, USA
  date: July 7-9, 2027                     # conference dates, free text
  sub: [ SYS ]                             # categories, see _data/types.yml
  # note: ...                              # optional free text under the entry
```

Use an IANA timezone (`America/New_York`, `America/Los_Angeles`) rather than a fixed offset when
the CFP says something like "5pm Pacific" — the offset changes with daylight saving and a fixed
`UTC-7` will be an hour off for half the year.

4. Validate before opening a pull request:

```bash
python3 scripts/validate.py
```

To add a category, edit `_data/types.yml` — the filter dropdown and the tag colors are generated
from it.

## Scripts

```bash
python3 scripts/validate.py                 # schema, unique ids, categories, timezones, date formats
python3 scripts/upcoming.py                 # every open deadline, soonest first
python3 scripts/upcoming.py --days 60 --sub SYS
```

## Local development

```bash
bundle install
bundle exec jekyll serve
# http://127.0.0.1:4000/cs-system-conf-deadline/
```

The site is built and deployed by `.github/workflows/pages.yml` on every push to the default
branch (plain Jekyll, so the plugin in `_plugins/` runs). `.github/workflows/validate.yml` runs the
data validator on pull requests.

## Calendar export

Every deadline (including abstract deadlines) is published as an iCalendar feed at
`/cs-system-conf-deadline/deadlines.ics`, generated from the same YAML by `_layouts/calendar.ics`.
Subscribe to it rather than copying dates by hand.

## License

MIT — see [LICENSE](LICENSE). Original copyright Abhishek Das and Jinwoo Hwang.
