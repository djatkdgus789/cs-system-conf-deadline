# CS System Conference Deadlines

Countdowns to computer **systems**, **architecture**, **ML systems**, **HPC**, **database** and
**networking** conference deadlines.

Built on [ai-deadlines](https://github.com/abhshkdz/ai-deadlines) by
[abhshkdz](https://github.com/abhshkdz), via the
[KAIST CASYS fork](https://github.com/casys-kaist/casys-kaist.github.io). The site machinery is
the same; the conference list is the part that is specific to this repository.

## What's tracked

| Category | Tag | Conferences |
| --- | --- | --- |
| System | `SYS` | SOSP, OSDI, SIGOPS ATC, EuroSys, NSDI, FAST, SoCC, Middleware, APSys, HotOS, SIGMETRICS, ICDCS, CLOUD, MASCOTS, SYSTOR, VEE, DSN, RTAS, SenSys, MMSys |
| Architecture | `ARCH` | ISCA, MICRO, ASPLOS, HPCA, PACT, ICS, ISPASS, IISWC, DAC, DATE, FPGA |
| ML System | `MLSYS` | MLSys, EuroMLSys |
| HPC | `HPC` | SC, PPoPP, IPDPS, HPDC, ICPP, CLUSTER, CCGrid, Euro-Par |
| Database | `DB` | SIGMOD, PODS, VLDB, ICDE, EDBT, DASFAA, BigData |
| Network | `NET` | SIGCOMM, CoNEXT, HotNets, IMC |

The data covers the deadlines that are still open as of September 2026 — mostly the 2027 editions,
plus the 2028 round for series whose 2027 deadlines have already closed.

## Official vs. projected deadlines

Entries carry a `tba: true` flag and a **projected** badge when the official CFP has not been
released and the date is extrapolated from the previous edition. Those dates move; treat them as a
planning hint, not a commitment, and **always confirm on the conference website before submitting.**
Entries without the badge come from a published CFP.

When a real CFP appears, replace the dates, drop `tba: true`, and drop the `note:` line.

## Adding or updating a conference

1. Edit the file under `_data/conferences/` named after the **conference year**, not the submission
   year (`2027.yml` holds a deadline in December 2026 for a conference held in July 2027).
2. One entry per deadline. A conference with several rounds gets several entries
   (`EuroSys (Fall)`, `SIGMOD (Round 4)`, …), each with its own unique `id`.

```yaml
- title: OSDI                              # short name shown in the list
  year: 2027                               # conference year
  id: osdi27                               # unique, lower case; used in URLs and CSS ids
  full_name: USENIX Symposium on Operating Systems Design and Implementation
  link: https://www.usenix.org/conference/osdi27/call-for-papers
  abstract_deadline: "2026-12-01 17:59:59" # optional
  deadline: "2026-12-08 17:59:59"          # or "TBA"
  timezone: America/New_York               # AoE, UTC, UTC-4, PST, or an IANA name
  place: Baltimore, MD, USA
  date: July 7-9, 2027                     # conference dates, free text
  sub: [ SYS ]                             # categories, see _data/types.yml
  # tba: true                              # set when the dates are projected
  # note: ...                              # optional free text under the entry
```

3. Validate before opening a pull request:

```bash
python3 scripts/validate.py
```

To add a category, edit `_data/types.yml` — the filter dropdown and the tag colors are generated
from it.

## Scripts

```bash
python3 scripts/validate.py          # schema, unique ids, categories, timezones, date formats
python3 scripts/upcoming.py          # every open deadline, soonest first
python3 scripts/upcoming.py --days 60 --sub SYS --official
```

`--official` hides the projected entries, which is what you want when deciding where to actually
submit.

## Local development

```bash
bundle install
bundle exec jekyll serve
# http://127.0.0.1:4000/cs-system-conf-deadline/
```

The site is built and deployed by `.github/workflows/pages.yml` on every push to `main`
(plain Jekyll, so the plugin in `_plugins/` runs). `.github/workflows/validate.yml` runs the data
validator on pull requests.

## Calendar export

Every deadline (including abstract deadlines) is published as an iCalendar feed at
`/cs-system-conf-deadline/deadlines.ics`, generated from the same YAML by `_layouts/calendar.ics`.
Subscribe to it rather than copying dates by hand.

## License

MIT — see [LICENSE](LICENSE). Original copyright Abhishek Das and Jinwoo Hwang.
