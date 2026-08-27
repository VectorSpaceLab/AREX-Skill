# Public Interface and Scope

## Purpose

Read this when deciding what labelme can promise as stable. labelme is an
application first, not a library package; the supported surface is the command
line, the on-disk Annotation File format, and the YAML Config File.

## Stable surfaces

- `labelme` console entry point and `python -m labelme` startup path.
- JSON Annotation Files (`.json`) written and read by the GUI and export
  scripts.
- The YAML Config File (`~/.labelmerc` by default, or a path supplied via
  `--config`).
- The `--labels` and `--flags` command-line sources for session label/flag
  vocabularies.
- Example conversion workflows that read labelme JSON and emit datasets.

## Not stable

- Python imports under `labelme.*` other than the CLI, config, and data-format
  helpers used by bundled skill scripts.
- Widget classes, internal automation helpers, and canvas internals.
- Private source layout under `_widgets/`, `_automation/`, `_utils/`, and other
  internal modules.

## Verified facts for this checkout

- Python support floor: 3.12.
- Qt binding: PySide6 6.8+.
- `labelme --help` shows `--output`, `--config`, `--flags`, `--label-flags`,
  `--labels`, `--validate-label`, `--keep-prev`, and `--epsilon`.
- `--output` must name a directory unless it is a single JSON Annotation File.
- `--config` accepts either a file path or an inline YAML mapping string.
- `validate_label=exact` requires predefined labels.
- `labelme` v7 uses YAML 1.2 behavior; booleans like `yes`/`no` are strings,
  not booleans.

## When to read

- Before explaining what users can rely on long term.
- Before writing bundled scripts that should survive future internal refactors.
- Before using or refreshing the skill for another labelme checkout.
