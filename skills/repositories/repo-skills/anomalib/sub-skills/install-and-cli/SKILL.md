---
name: install-and-cli
description: "Covers Anomalib installation choices, the install subcommand, CLI
  help behavior, config loading, and command selection for fit, validate, test,
  train, predict, export, and benchmark."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Install and CLI

Use this sub-skill when the user wants to install Anomalib, understand the `anomalib install` subcommand, inspect CLI help, load configs, or choose between `fit`, `validate`, `test`, `train`, `predict`, `export`, and `benchmark`.

## Read first

- For install matrices, backend selection, editable installs, and when to use direct package install versus `anomalib install`, read [references/installation.md](references/installation.md).
- For the command map, config-loading rules, help verbosity, and export flag selection, read [references/cli-reference.md](references/cli-reference.md).
- For missing-backend, config-path, help-verbosity, or export-flag failures, read [references/troubleshooting.md](references/troubleshooting.md).
- For a read-only CLI smoke check, run [scripts/check_cli_help.sh](scripts/check_cli_help.sh).
- For copyable install, training, prediction, export, and benchmark recipes, run [scripts/cli_recipes.sh](scripts/cli_recipes.sh).

## Safe operating boundary

This sub-skill stays at the command, installation, and routing layer.

It covers:

- package installation choices for CPU and OpenVINO support;
- `anomalib install` options and when they are appropriate;
- top-level help output, verbose help formatting, and config-file loading;
- command selection for `fit`, `validate`, `test`, `train`, `predict`, `export`, and `benchmark`.

It does not cover:

- model math, dataset schemas, export internals, or training loops;
- benchmark pipeline mechanics beyond choosing the `benchmark` command;
- Studio or UI application code.

## Quick routing

| User need | Route here? | Read or run |
| --- | --- | --- |
| Smallest CPU plus OpenVINO install | Yes | Read [references/installation.md](references/installation.md), then print commands with [scripts/cli_recipes.sh](scripts/cli_recipes.sh) |
| Decide between `anomalib install` and `pip`/`uv` | Yes | Read [references/installation.md](references/installation.md) |
| Explain why `anomalib -h` only shows `install` | Yes | Read [references/troubleshooting.md](references/troubleshooting.md) |
| Check top-level help, install help, and verbose help behavior | Yes | Run [scripts/check_cli_help.sh](scripts/check_cli_help.sh) |
| Choose `fit` vs `train` vs `validate` vs `test` | Yes | Read [references/cli-reference.md](references/cli-reference.md) |
| Choose `predict` or recover from old `--data_path` examples | Yes | Read [references/cli-reference.md](references/cli-reference.md) and [references/troubleshooting.md](references/troubleshooting.md) |
| Diagnose export flags, especially OpenVINO options | Yes | Read [references/cli-reference.md](references/cli-reference.md) and [references/troubleshooting.md](references/troubleshooting.md) |
| Understand benchmark routing or benchmark config semantics | Partly | Route the command choice here, then hand off to the sibling `pipelines-and-benchmarks` sub-skill for workflow details |

## Operating notes

- Use direct package install when the user is bootstrapping a fresh environment or needs a specific backend wheel.
- Use `anomalib install` only after Anomalib is already installed and the user wants to add optional bundles such as `openvino`, `loggers`, or `notebooks`.
- Treat `cpu` as a package extra, not as an `anomalib install --option` value.
- Prefer the current `--data` syntax for prediction examples; older `--data_path` shell snippets are legacy and should be translated before reuse.
- If a config file names the right subcommand but the wrong model or data class path, diagnose it as a command/config mismatch rather than a parser failure.
- If the benchmark command is missing, check whether the pipeline module is importable before assuming the CLI is broken.

## Recommended workflow

1. Confirm whether the user needs a fresh install, an editable source install, or an add-on bundle inside an existing environment.
2. Read the installation reference and pick the smallest command that satisfies the backend.
3. Run the CLI smoke helper after installation or dependency changes.
4. Use the CLI reference to choose the right subcommand and flags.
5. Escalate to troubleshooting when help output, config loading, or export flags do not match the expected command shape.
