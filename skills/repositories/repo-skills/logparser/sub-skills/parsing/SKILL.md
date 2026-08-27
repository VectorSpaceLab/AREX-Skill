---
name: parsing
description: "Guides Logparser log-template extraction, ordinary parser
  selection, output CSV inspection, and template matching workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Parsing

Use this sub-skill for the ordinary log-template extraction path.
It covers the parsers that follow the standard `LogParser` pattern and the
`logmatch` template-matching workflow.

## Include here

- Custom log parsing with Drain as the default example.
- Ordinary parser selection: Drain, AEL, IPLoM, LKE, LFA, LogSig, LenMa,
  LogMine, Spell, Logram, Brain, and ULP.
- Output inspection for `EventId`, `EventTemplate`, `Occurrences`, and
  `ParameterList`.
- Matching logs against already extracted templates with `logmatch`.

## Exclude from here

- Benchmark and evaluation flows; use `../benchmarking/SKILL.md`.
- Parsers with special shims, compilers, CUDA/torch, API keys, or non-default
  dependencies; use `../specialized-parsers/SKILL.md`.
- Maintainer-only repository changes.

## Read these references

- `references/workflows.md` for the ordinary parse and template-match recipes.
- `references/api-reference.md` for the inspected constructor summaries.
- `references/troubleshooting.md` for format mismatches, output quirks, and
  template-matching failures.

## Run these scripts

- `scripts/parse_tiny_drain.py` — safe tiny Drain smoke or starter template.
- `scripts/match_templates.py` — match logs against a templates CSV.

## When to route here

Choose this sub-skill when the request says things like:

- "parse my logs"
- "use Drain"
- "extract templates"
- "convert raw logs into structured CSVs"
- "match logs against templates"
- "show the EventId/EventTemplate output"

## Working notes

- Start with `scripts/check_install.py` if the environment has not been
  inspected yet.
- When a parser returns only a structured CSV or a template CSV, follow the
  parser-catalog and troubleshooting references rather than assuming the output
  shape is broken.
- If `logmatch` raises a `bad escape \s` error, prefer `scripts/match_templates.py` because it patches the legacy loader replacement at runtime.
- Keep the original repo checkout out of runtime instructions; use the bundled
  skill scripts and references.
