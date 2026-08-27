---
name: cli-settings
description: "Use Vaex's console commands and configuration safely: discover CLI
  capabilities, inspect datasets, manage aliases, and diagnose effective
  settings without accidental mutation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# cli-settings

Use this sub-skill when the task concerns the installed `vaex` console command,
CLI diagnostics, `vaex open`/`stat` checks, aliases, or repeatable Vaex
configuration through environment variables, runtime settings, `.env`, or the
Vaex home YAML file.

## Read order

1. Read [references/cli-reference.md](references/cli-reference.md) for command
   discovery, exit-code interpretation, safe flags, and routing boundaries.
2. Read [references/configuration.md](references/configuration.md) for settings
   fields, environment-variable naming, precedence, YAML/JSON/schema output,
   and persistence cautions.
3. Read [references/troubleshooting.md](references/troubleshooting.md) when a
   console entry point, optional command, settings representation, alias, or
   file-open check fails.

## Safe diagnostics

- Start with `vaex --help`, then the relevant subcommand help. Use `vaex version`
  to confirm the installed package without opening data.
- Prefer `vaex open --dry-run --verbose PATH` for file-open diagnostics. Do not
  add `--delete`: that flag removes inputs that fail to open. `--dry-run` only
  prevents the destructive action; it does not make an invalid input valid.
- Use `vaex stat PATH` for read-only dataset metadata. It still opens the input,
  so treat remote or credentialed paths as an explicit trust-boundary decision.
- Use `vaex alias list` for inspection. `alias add` and `alias remove` change
  the user's alias mapping; obtain approval before running either.
- Use [scripts/vaex_cli_smoke.py](scripts/vaex_cli_smoke.py) for a bounded,
  local console check. Use [scripts/vaex_settings_probe.py](scripts/vaex_settings_probe.py)
  for read-only settings summaries. Run each helper with `--help` first.

## Configuration safety

- Set environment variables before importing Vaex when reproducible process
  configuration matters. Runtime assignments such as
  `vaex.settings.main.thread_count = 4` affect the current process only unless
  explicitly saved.
- Treat `vaex settings save`, `save-defaults`, and `set` as configuration
  writes. The current CLI's `set` spelling saves effective non-default values;
  do not assume it accepts key/value arguments.
- Treat `vaex settings docgen` and `watch` as developer-only operations. They
  write documentation and/or run a long-lived watcher and should not be used as
  ordinary diagnostics. `benchmark` and `test` are maintainer/expensive entry
  points, not health checks.
- Do not paste raw settings output into shared material: defaults can contain
  machine-specific home, cache, lock, data, or filesystem paths.

## Routing boundaries

- Route `vaex convert` format semantics, conversion cleanup, filters/columns,
  chunking, and roundtrip validation to
  [../io-conversion/SKILL.md](../io-conversion/SKILL.md).
- Route `vaex server`/`vaex webserver` startup, dataset naming, endpoints,
  tokens, GraphQL, and local service checks to
  [../serving-remote/SKILL.md](../serving-remote/SKILL.md).
- Route Python `vaex.open`, DataFrame construction, lazy evaluation, filtering,
  and virtual columns to
  [../dataframe-core/SKILL.md](../dataframe-core/SKILL.md).
- Route expression syntax, analytic filters, and aggregate validation to
  [../expressions-analytics/SKILL.md](../expressions-analytics/SKILL.md).
