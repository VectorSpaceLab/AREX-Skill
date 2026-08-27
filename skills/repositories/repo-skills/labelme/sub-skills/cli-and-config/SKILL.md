---
name: cli-and-config
description: "Guides labelme CLI startup, GUI session configuration, label and
  flag sources, YAML Settings, output paths, and display-related recovery."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# CLI and Config

Use this route when the task is to launch labelme, choose annotation-session
options, configure labels/flags, control saving or navigation, or debug a
Config File and GUI startup.

## Workflow

1. Confirm Python 3.12+ and install `labelme` in the target environment.
2. Run `labelme --help` and `labelme --version` before opening a GUI.
3. Choose a path (image, Annotation File, or directory), then add only the
   needed flags. Read `references/cli-reference.md` for exact behavior.
4. Use `--labels` and `--flags` with comma-separated values or a text file;
   use `--label-flags` for YAML label-specific Shape Flags.
5. Use `--output` as a directory for a session, not a `.json` filename, unless
   the behavior is intentionally a single target as described in the CLI ref.
6. Use `--config <file>` for a writable Config File or `--config '{...}'` for
   ephemeral session overrides. Inspect a candidate without writing it with
   `scripts/inspect_labelme_config.py`.
7. If `--validate-label exact` is enabled, provide a non-empty label list.
8. If the GUI fails, prove the CLI parser works, then check display/Qt setup;
   read `references/troubleshooting.md`.

## Config rules that matter

- Defaults live in the shipped Default Config; the user Config File is sparse
  YAML Overrides, normally `~/.labelmerc`.
- GUI Settings apply immediately and preserve comments where possible.
- A CLI override or inline YAML makes that session's settings non-editable;
  use a file if interactive Settings editing is required.
- YAML 1.2 means `true`/`false` are booleans; `yes`/`no`/`on`/`off` are strings.
- `canvas.allow_out_of_bounds_points` is opt-in and preserves negative or
  beyond-image coordinates for partially visible objects.
- Window State (geometry/docks) is separate Qt `QSettings` state; `--reset-config`
  clears that state and is not a substitute for editing YAML Overrides.

## References and helper

- Read `references/cli-reference.md` for flags and output semantics.
- Read `references/configuration.md` for Settings groups, migration behavior,
  YAML examples, and validation constraints.
- Read `references/troubleshooting.md` for install, Qt/display, and malformed
  config recovery.
- Run `scripts/inspect_labelme_config.py --config-yaml '{labels: [cat]}' --show labels`
  to validate an inline mapping without writing a Config File.

Route JSON schema questions to `../annotation-data/SKILL.md`, conversion
questions to `../dataset-export/SKILL.md`, AI model/prompt questions to
`../ai-assisted-annotation/SKILL.md`, and source/test changes to
`../repo-development/SKILL.md`.
