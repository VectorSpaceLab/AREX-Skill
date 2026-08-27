---
name: cli-and-automation
description: "Run NannyML from the command line, load config files, schedule
  repeated runs, and persist results or fitted calculators."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# CLI and Automation

Use this sub-skill when the task is about the `nml` CLI, config-file discovery, configuration loading, scheduled runs, output writers, or reusing fitted calculators through the filesystem store.

Route calculator-specific performance, drift, or data-quality questions to the matching monitoring sub-skill unless the main task is command construction, config wiring, or persistence.

## Quick routing

- Read [references/cli-reference.md](references/cli-reference.md) for command syntax, config-path discovery, and the config-loading behavior that affects `nml run --help`.
- Read [references/configuration.md](references/configuration.md) for the current code-backed YAML schema: `input`, `calculators`, `scheduling`, `ignore_errors`, per-calculator `params`, `outputs`, and `store`.
- Read [references/io-and-store.md](references/io-and-store.md) for `FileReader`, `RawFilesWriter`, `PickleFileWriter`, `FilesystemStore`, and optional `DatabaseWriter` behavior.
- Read [references/troubleshooting.md](references/troubleshooting.md) when errors mention `NML_CONFIG_PATH`, config discovery, malformed scheduling blocks, missing filenames, unsupported file suffixes, cloud credentials, optional database dependencies, or the CLI help/config-load sequence.
- Read [../../references/results-and-plots.md](../../references/results-and-plots.md) when the question is really about result export shape rather than CLI wiring.

## What this sub-skill covers

- Using `nml --help`, `nml -c <config> run`, and `nml -c <config> run --help` safely.
- Finding the active config file with `-c`, `NML_CONFIG_PATH`, `/config/nannyml.yaml`, `/config/nann.yml`, `nannyml.yaml`, or `nann.yml`.
- Building calculator-by-calculator YAML with `input`, `calculators`, `outputs`, `store`, `scheduling`, and `ignore_errors`.
- Writing monitoring results to local or cloud files, pickled results, or databases.
- Persisting fitted calculators with `FilesystemStore` so repeated runs can reload instead of refit.
- Choosing one-off vs scheduled execution and validating cron/interval settings.

## Primary execution shapes

| Task | Use |
| --- | --- |
| Verify the CLI is installed and discover commands | `nml --help` or `nml -c <cfg> run --help` |
| Run one or more calculators on input files | `nml -c <cfg> run` |
| Load reference/analysis/target files from local or cloud storage | `input.reference_data`, `input.analysis_data`, `input.target_data` |
| Persist result tables | per-calculator `outputs:` with `raw_files`, `pickle`, or `database` writers |
| Cache fitted calculators | per-calculator `store:` with `FilesystemStore` settings |
| Re-run on a schedule | `scheduling.interval` or `scheduling.cron` |

## Minimum safe pattern

```python
# The CLI ultimately loads a config and calls runner.run(config=...)
# So the best mental model is "one config file, many calculators".
```

For a help-only smoke check, the runtime still needs a valid config file because the CLI callback loads configuration before the `run` subcommand help is rendered.

## Boundaries

- This sub-skill does not explain the internals of CBPE, DLE, drift methods, or data-quality formulas.
- If a task is really about choosing metrics, chunking, or thresholds, route to the monitoring/data-setup sub-skills and return here only to wire the calculator into a config.
- The skill is self-contained; do not require the user to open the source checkout or copy repo-private paths into the runtime config.
