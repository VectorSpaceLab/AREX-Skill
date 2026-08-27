# CLI Reference

## Commands

The installed console script is `nml`.

```bash
nml --help
nml -c /path/to/nannyml.yaml run
nml -c /path/to/nannyml.yaml run --help
nml --version
```

`nml` is a Click-based command group. The `run` subcommand triggers the monitoring runner. The root command loads configuration before the `run` command help body is displayed, so `run --help` still needs a valid config file.

## Configuration path discovery

The config path is resolved in this order:

1. `-c` / `--configuration-path`
2. `NML_CONFIG_PATH`
3. `/config/nannyml.yaml`
4. `/config/nann.yml`
5. `nannyml.yaml` in the current working directory
6. `nann.yml` in the current working directory

If none of those exist, configuration loading fails.

## Config-file names

Supported filenames at the discovery locations are:

- `nannyml.yaml`
- `nann.yml`

## `run` command behavior

- Without `scheduling`, the CLI runs once and exits.
- With `scheduling.interval` or `scheduling.cron`, the CLI starts a blocking scheduler.
- The scheduler currently supports one scheduling subsection at a time.
- `run` logs progress through the console when the command is executed interactively.

## Smoke-check pattern

A minimal config that is sufficient for `nml -c <cfg> run --help` can be as small as:

```yaml
calculators:
  - type: missing_values
    params:
      column_names: [feature]
```

Use this shape for help checks only. Real runs also need input data and calculator parameters that match the chosen monitor.

## Useful shell commands

```bash
# show the CLI and available commands
nml --help

# use an explicit config path
nml -c ./nannyml.yaml run

# inspect the run-specific help after loading config
nml -c ./nannyml.yaml run --help
```
