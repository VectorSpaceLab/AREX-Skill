---
name: cli-workflows
description: "Guide Snips NLU CLI command construction for datasets, training,
  parsing, resources, versions, and metrics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# CLI Workflows

Use this sub-skill when a user needs to construct, check, or troubleshoot
`snips-nlu` / `python -m snips_nlu` commands for Snips NLU 0.20.x workflows:
dataset JSON generation, engine training, one-shot or interactive parsing,
language-resource downloads, manual resource linking, version checks, or CLI
metrics.

## Route Quickly

1. Start with the safe availability check in
   [`scripts/snips_nlu_cli_smoke.py`](scripts/snips_nlu_cli_smoke.py). It only
   runs version commands and `--help` checks by default; it does not download
   resources, train, parse, or write model outputs.
2. Use [`references/cli-reference.md`](references/cli-reference.md) for command
   grammar, required positional arguments, shell quoting, resource-management
   commands, and end-to-end command templates.
3. Use [`references/evaluation.md`](references/evaluation.md) when the task is
   `cross-val-metrics` or `train-test-metrics`, especially if the optional
   metrics dependency may be missing.
4. Use [`references/troubleshooting.md`](references/troubleshooting.md) when a
   command fails, when downloads require network or pip options, when parse
   cannot load a trained engine, or when an output path already exists.

## Boundaries

- Dataset YAML/JSON schema, builtin/custom entity data format, and resource
  naming concepts belong in `../dataset-and-resources/SKILL.md`.
- Programmatic alternatives using `SnipsNLUEngine`, `Dataset.from_yaml_files`,
  `load_resources`, or `NLUEngineConfig` belong in `../engine-api/SKILL.md`.
- This sub-skill owns CLI command construction and operational safeguards only;
  do not duplicate full dataset schema or API reference material here.

## Default Entry Point Policy

Prefer `python -m snips_nlu` when the console script is missing or the active
Python environment is ambiguous. Use `snips-nlu` when it is available and known
to resolve to the intended Snips NLU installation. Both entry points expose the
same subcommands for the workflows covered here.
