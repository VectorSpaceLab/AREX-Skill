---
name: cli-datasets-config
description: "Guides MNE-Python CLI entry points, dataset helpers,
  configuration, logging, system information, cache/network decisions, and
  install extras."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# MNE-Python CLI, datasets, and configuration router

Use this sub-skill when the task is about the `mne` console entry point, MNE-supplied dataset location/download decisions, persistent MNE configuration, logging, system diagnostics, cache/memmap settings, or choosing installation extras.

## Route by task

- Command discovery, `mne --help`, `mne --version`, `mne sys_info`, `mne show_info`, `mne what`, `mne report`, and source/BEM setup commands: read [CLI reference](references/cli-reference.md).
- Dataset helpers, no-download checks, `MNE_DATA`, dataset-specific config keys, `get_config`, `set_config`, `get_config_path`, logging, cache, memmap, and `sys_info`: read [datasets and config](references/datasets-and-config.md).
- Installing core versus full MNE-Python, HDF5 support, Qt variants, optional dependencies, and development extras: read [installation and extras](references/installation-and-extras.md).
- Invalid commands, missing console script, missing datasets, network/cache/hash issues, config-file problems, and optional-dependency failures: read [troubleshooting](references/troubleshooting.md).
- To verify a user's environment without running analysis or downloading data, run the bundled helper: `python scripts/mne_cli_probe.py --help`, then select safe probes.

## Boundaries

This sub-skill owns package operation and environment decisions. Route detailed Python data analysis, preprocessing, visualization, source modeling, statistics, decoding, or simulation workflows to their owning analysis sub-skills. Route repository editing, linting, changelog, contributor policy, and native test-selection policy to `repo-development`.

## Safe default operating pattern

1. Start with `mne --help`, `mne --version`, and `mne sys_info --help`; use `mne sys_info --no-check-version --ascii` when network access or Unicode output is a concern.
2. Before a command can write files or open a GUI, inspect `mne <command> --help` and identify input/output paths, overwrite flags, display requirements, and optional dependencies.
3. For datasets, avoid accidental downloads in planning or tests: call dataset helpers with `download=False` and `update_path=False`, then treat an empty path result as "not available locally".
4. For persistent settings, prefer `mne.get_config_path()`, `mne.get_config()`, and `mne.set_config()` rather than editing config JSON directly.
5. Do not paste `sys_info(show_paths=True)` output publicly until local paths have been reviewed for privacy.

## Evidence provenance

Distilled from MNE-Python command modules, dataset utilities, config/logging utilities, install metadata, install documentation, command and dataset tests, and installed CLI/API smoke evidence. Runtime use of this skill does not require opening those source files.
