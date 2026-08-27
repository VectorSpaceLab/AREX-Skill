---
name: cli-config-data
description: "Operate Astropy installation checks, optional extras,
  configuration/cache paths, remote data and IERS policy, logging/warnings,
  SAMP, and public command-line tools."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# CLI, Config, and Data Operations Router

Use this sub-skill for operational Astropy tasks that cut across modules:
installation, import checks, optional extras, configuration, cache/remote data,
IERS, logging, warnings, SAMP, and the public command-line catalog.

## Load This When

- The task asks how to install Astropy, choose extras, verify imports, or check
  console command availability.
- The user needs configuration directories, cache directories, temporary config
  or cache contexts, environment variables, logging, or warning control.
- The task mentions IERS tables, remote downloads, name resolving, offline
  operation, or cache refresh/removal.
- The task uses SAMP hub/client workflows or the `samp_hub` command.
- The user needs a command catalog for `fitsinfo`, `fitsheader`, `fitscheck`,
  `fitsdiff`, `fits2bitmap`, `showtable-astropy`, `volint`, `wcslint`, or
  `samp_hub`.

## Route Away When

- Detailed FITS/table data operations dominate; use `../tables-io/SKILL.md`.
- WCS lint output and pixel/world validation dominate; use
  `../wcs-nddata/SKILL.md`.
- FITS bitmap rendering choices dominate; use
  `../visualization-convolution/SKILL.md`.
- Scientific API usage is in one domain; route to that domain sub-skill.

## First Actions

1. Identify whether the task is install/import, config/cache, remote data,
   logging/warnings, SAMP, or CLI execution.
2. Use the smallest install extra that satisfies the task.
3. For offline/reproducible runs, set remote-data/IERS policy before executing
   coordinate/time code.
4. Run `--help` for CLIs before forming mutating commands.
5. Use temporary files for CLI smoke checks and never mutate user FITS/table
   files without explicit approval.
6. Capture warnings by class and source rather than suppressing all warnings.

## References

- [references/operations.md](references/operations.md) covers installation,
  config/cache, remote-data/IERS, logging, warnings, and SAMP operations.
- [references/cli-reference.md](references/cli-reference.md) summarizes public
  commands, ownership, and safety notes.
- [references/troubleshooting.md](references/troubleshooting.md) covers common
  operational failures and recovery steps.
- Root scripts [../../scripts/astropy_smoke.py](../../scripts/astropy_smoke.py)
  and [../../scripts/astropy_cli_smoke.py](../../scripts/astropy_cli_smoke.py)
  provide safe installed-package checks.

## Safety and Validation

- Do not enable network downloads implicitly for offline tasks.
- Do not start long-running services such as a SAMP hub unless the user asks.
- Treat `fitscheck` and output-producing CLIs as potentially mutating; use
  copies and explicit output paths.
- Keep environment-specific paths out of final user instructions unless the
  user supplies them for the current task.

## Native-Backed Validation Ideas

- Run root smoke scripts against an installed package.
- Run `--help` for all public Astropy console commands.
- Temporarily set `iers.conf.auto_download = False` and confirm coordinate/time
  workflows can run with bundled data where sufficient.
