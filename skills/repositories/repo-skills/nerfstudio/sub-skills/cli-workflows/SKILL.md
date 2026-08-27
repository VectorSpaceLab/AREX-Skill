---
name: cli-workflows
description: "Routes Nerfstudio installation, console entry points,
  help-ordering, tab completion, and safe dataset-download preflight tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# CLI Workflows

Use this route for the first interaction with a Nerfstudio environment: install,
inspect, and choose the right `ns-*` command before doing data conversion,
training, viewer, or export work.

## What this route covers

- Public console entry points from the package metadata: `ns-install-cli`, `ns-process-data`, `ns-download-data`, `ns-train`, `ns-viewer`, `ns-eval`, `ns-render`, `ns-export`, `ns-dev-test`, and `ns-dev-sync-viser-message-defs`.
- The argument-order rule for tyro: method flags come after the method name and dataparser flags come after the dataparser name.
- Safe install and preflight checks for a working Python environment and the common optional binaries that shape later workflows.
- Shell completion installation planning without mutating user shell state inside the skill.

## What this route excludes

- Real data conversion, validation, or path-fixing: use `data-preparation`.
- Method choice, config overrides, resume logic, or multi-GPU training: use `training-and-configs`.
- Viewer startup, rendering, metrics, or export work: use `visualization-and-export`.
- Custom method/dataparser registration: use `api-extension`.

## Read these bundled files when needed

- [`references/cli-reference.md`](references/cli-reference.md) for the command catalog and the argument-order rule.
- [`references/installation-and-backends.md`](references/installation-and-backends.md) for Python, CUDA, and optional-binary notes.
- [`references/troubleshooting.md`](references/troubleshooting.md) when help output, imports, or external binaries fail.
- [`scripts/inspect_ns_cli.py`](scripts/inspect_ns_cli.py) to print installed `ns-*` commands and verify safe `--help` behavior.

## Usual workflow

1. Run the bundled inspector or a safe `--help` check.
2. Confirm that the command exists in the current environment.
3. Route the task to the next skill once the command family is identified.
4. For downloads or processing, stop at the preflight stage until the required external tools and data are available.

## Common signals

- `ns-train --help` shows available built-in methods and external install hooks.
- `ns-process-data --help` lists the dataset conversion modes and their path/data arguments.
- `ns-export --help` lists point cloud, mesh, camera, and Gaussian Splat export subcommands.
- `ns-viewer --help` confirms the viewer config surface without opening a service.
