---
name: electricitymaps-contrib
description: "Use for Electricity Maps contrib parser development, capacity
  updates, zone/exchange configuration maintenance, and focused repo validation
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Electricity Maps Contrib

Use this skill when working on the `electricitymaps-contrib` repository or the
`electricitymap-contrib` Python package. The repo collects and standardizes
public electricity data through live parsers, installed-capacity parsers, and
static zone/exchange configuration files.

Do not use this skill for the proprietary Electricity Maps platform, frontend,
API access decisions, or generic electricity-market analysis that does not touch
this repository's parser/configuration workflows.

## Start here

1. Confirm the checkout is for `electricitymaps/electricitymaps-contrib` and
   compare it with [repo provenance](references/repo-provenance.md) before
   trusting stale paths, parser names, or config fields.
2. Install for development with `uv sync --extra parsers --group dev` when
   possible. If a toolchain cannot use dependency groups, read
   [installation and checks](references/installation-and-checks.md) for the pip
   fallback and the difference between the `parsers` extra and dev tools.
3. Run the bundled import diagnostic before debugging path-sensitive parser
   imports:

   ```bash
   python scripts/check_environment.py --repo-root <electricitymaps-contrib-checkout>
   ```

4. Pick the owning sub-skill below. Keep runtime work anchored in the current
   checkout; the references and scripts in this skill replace the need to open
   the original source docs or scripts by path.

## Route by task

| User task | Read next |
| --- | --- |
| Add, repair, inspect, or smoke-test a live parser for production, consumption, price, exchange, forecast, grid alerts, LMP, or intraday statistics | [parsers](sub-skills/parsers/SKILL.md) |
| Diagnose parser output shape, parser signature, timezone, missing token, optional dependency, or `test-parser` behavior | [parsers](sub-skills/parsers/SKILL.md) and [parser troubleshooting](sub-skills/parsers/references/troubleshooting.md) |
| Update installed capacity values, run `capacity_update`, add a capacity parser, or review capacity time-series semantics | [capacity](sub-skills/capacity/SKILL.md) |
| Understand capacity config scalar/dict/list formats, aggregate parent-zone capacity rules, or source-group updates such as EIA/EMBER/ENTSOE/IRENA/ONS/OPENNEM/REE | [capacity](sub-skills/capacity/SKILL.md) |
| Edit or validate `config/zones`, `config/exchanges`, data-center JSON, emission-factor/co2eq config, filename ordering, or geometry consistency | [configuration](sub-skills/configuration/SKILL.md) |
| Create an aggregate zone config, validate zone/exchange filenames, or plan safe zone removal/retirement | [configuration](sub-skills/configuration/SKILL.md) |
| Install/import failures, missing CLI entry points, missing parser extras, Node/prettier issues, or token/network boundaries shared across workflows | [repo troubleshooting](references/troubleshooting.md) |

## Repo-wide operating rules

- Prefer focused checks before broad test runs: parser changes usually start
  with the parser smoke helper and `tests/test_parser_interface.py`; capacity
  changes start with capacity helper tests; config changes start with config
  model and filename/geo tests.
- Treat live parser and capacity-update execution as network/API-token work.
  Use mocked native tests or script `--list`/`--describe`/dry-run modes until
  the user has approved live calls and credentials are available.
- `productionCapacity` belongs to the capacity route, not the live-parser
  smoke route. It has a different signature and mutates installed-capacity
  config through update helpers.
- When a task changes YAML/JSON config, inspect the diff before formatting and
  run the nearest validation commands from [installation and checks](references/installation-and-checks.md).
- Do not bulk-update all capacities, zone names, or zone removals by default.
  The repository's own docs prefer small reviewable PRs and several legacy
  scripts are intentionally not safe as default helpers.

## Skill-owned references and scripts

- [installation-and-checks.md](references/installation-and-checks.md) explains
  install variants, console scripts, and focused native validation commands.
- [troubleshooting.md](references/troubleshooting.md) covers cross-cutting
  import, dependency, token, prettier, and path-normalization failures.
- [repo-routing-metadata.json](references/repo-routing-metadata.json) is
  structured metadata for a future managed repo-skill import; ordinary task
  execution does not need to read it.
- `scripts/check_environment.py` verifies the package, parser namespace,
  config model, console entry points, and common optional imports without live
  network calls.
