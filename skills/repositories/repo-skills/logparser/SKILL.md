---
name: logparser
description: "Routes agents through Logparser log-template extraction, parser
  selection, benchmark evaluation, and special parser dependency workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Logparser

Use this skill for the `logparser3` toolkit and its bundled log parsing algorithms.
It covers:

- parsing raw logs into event templates and structured CSVs,
- matching logs against already extracted templates,
- running Loghub benchmark/evaluation flows,
- handling parser-specific dependencies, import shims, compilers, GPUs, and API-backed flows.

## Start here

1. Read `references/repo-provenance.md` if you need to check whether this skill still matches the checkout.
2. Run `scripts/check_install.py` to confirm the active environment, package versions, parser imports, and backend helpers.
3. Choose the right route:
   - `sub-skills/parsing/` for ordinary parsers and template matching.
   - `sub-skills/benchmarking/` for benchmark and evaluator workflows.
   - `sub-skills/specialized-parsers/` for SHISO, SLCT, LogCluster, MoLFI, NuLog, DivLog, and other non-default dependency paths.

## Install and inspect

For a fresh checkout, the usual editable install is:

```bash
python -m pip install -e .
python scripts/check_install.py
```

If you only need the published package instead of the checkout, `pip install logparser3` is the public install path.
The generated skill stays self-contained by relying on its own bundled references and scripts rather than the original repo docs or demos.

## Routing map

### Parsing
Choose `sub-skills/parsing/` when the user wants to:

- parse custom logs with Drain or another ordinary parser,
- understand constructor arguments such as `log_format`, `indir`, `outdir`, `rex`, `depth`, `st`, or `support`,
- inspect `EventId`, `EventTemplate`, or `ParameterList` outputs,
- match parsed templates back onto logs with `logmatch`.

### Benchmarking
Choose `sub-skills/benchmarking/` when the user wants to:

- run or adapt benchmark scripts,
- compare `F1_measure`, `Accuracy`, parsing accuracy, grouping accuracy, or template accuracy,
- evaluate `*_structured.csv` files against ground truth,
- interpret Loghub dataset layout and result files.

### Specialized parsers
Choose `sub-skills/specialized-parsers/` when the user wants to:

- use SHISO, SLCT, LogCluster, MoLFI, NuLog, or DivLog,
- work around the SHISO import shim,
- compile SLCT with modern GCC,
- manage CUDA / torch / OpenAI / Perl / compiler / API-key dependencies,
- diagnose parser-specific output quirks or missing files.

## Shared references

- `references/parser-catalog.md` for the parser map, import paths, constructor summaries, and ownership.
- `references/data-formats.md` for log-format syntax, output CSV columns, and dataset layout.
- `references/troubleshooting.md` for cross-cutting install, import, dependency, compile, CUDA, and API issues.
- `references/repo-provenance.md` for the snapshot used to create this skill.
- `references/repo-routing-metadata.json` for router import metadata.

## Shared scripts

- `scripts/check_install.py` — run this first for a quick environment, import, and backend sanity check. The bundled scripts bootstrap the repository root automatically, so you can invoke them by path from this checkout without pre-setting `PYTHONPATH`.

## Working rules

- Keep all runtime guidance inside this skill tree.
- Do not send future agents back to source-repo docs, demos, or test scripts for routine use.
- If a parser has a special dependency or import quirk, read the specialized sub-skill first before trying to force the ordinary parser route.
