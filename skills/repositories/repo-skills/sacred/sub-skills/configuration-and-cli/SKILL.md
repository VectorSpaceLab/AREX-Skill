---
name: configuration-and-cli
description: "Define, update, inspect, and troubleshoot Sacred configuration and
  experiment command lines."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Sacred Configuration And CLI

Use this sub-skill when the task is to define Sacred configuration, apply or inspect config updates, route experiment commands from the command line, or diagnose CLI/config parsing behavior for Sacred 0.8.7.

## Read and run map

- Read [references/configuration-and-cli.md](references/configuration-and-cli.md) when designing config scopes, config dictionaries/files, named configs, config hooks, API `config_updates`, or the order in which Sacred resolves configuration.
- Read [references/api-and-command-reference.md](references/api-and-command-reference.md) when translating a Python API run into CLI syntax, using built-in commands, choosing flags, adding a custom `cli_option`, or routing custom/ingredient commands.
- Read [references/troubleshooting.md](references/troubleshooting.md) when `with` arguments parse unexpectedly, `print_config` reports added/typechanged values, config keys are rejected, a `ConfigScope` fails, nested config is read-only, a command is unknown, or YAML config files fail.
- Run [scripts/sacred_config_cli_probe.py](scripts/sacred_config_cli_probe.py) after installing Sacred to verify the current Python can execute `print_config`, CLI updates, a named config, a custom command, and a custom CLI option without external services.

## Scope and routing

This sub-skill owns:

- `@ex.config` config scopes, `ex.add_config(...)`, config files, config dictionaries, `@ex.named_config`, `ex.add_named_config(...)`, and `@ex.config_hook`.
- Programmatic `Experiment.run(config_updates=..., named_configs=..., options=...)` and `Experiment.run_commandline(argv=...)` config behavior.
- CLI `with` updates, dotted notation, named configs, built-in commands, command routing, CLI flags, and custom `cli_option` handling.

Route elsewhere:

- Experiment object lifecycle, `Run` semantics, captured function internals, resources, and artifacts belong to `experiment-core`.
- Observer storage schemas, run directory contents, metrics, artifacts, and external observer setup belong to `observers-and-logging`.
- Reproducibility, dependency/source capture, stdout/stderr capture modes, clean repository enforcement, and randomness belong to `reproducibility-and-capture`.

## Fast operating pattern

1. Define defaults first with a config scope or `add_config`.
2. Add optional variants with named configs.
3. Use `print_config` before a real run to inspect the effective config and any suspicious changes.
4. Use quoted `with` updates for strings, lists, dictionaries, booleans, and nested dotted paths.
5. Prefer adding intentional new keys to the default config instead of relying on `--force`.
6. If a command fails to route, run `help` and `print_named_configs` before changing experiment code.
