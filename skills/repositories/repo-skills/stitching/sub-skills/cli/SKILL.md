---
name: cli
description: "Routes `stitch` command-line usage, flag selection, feature-mask
  validation, affine mode, verbose output, and headless or Docker command
  building for stitching panoramas."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# CLI

Use this sub-skill when a user wants to build or debug a `stitch` command-line
invocation rather than write Python code.

## Typical triggers

- "stitch these images from the shell"
- "what flags should I pass to `stitch`?"
- "I need affine mode or verbose output"
- "how do I use feature masks from the CLI?"
- "why does `stitch` fail in a headless session?"

## What this sub-skill owns

- The public `stitch` entry point.
- Positional image arguments, glob patterns, and output paths.
- `--affine`, `--verbose`, `--verbose_dir`, `--output`, `--output_params`.
- Feature and matcher tuning flags such as `--detector`, `--nfeatures`,
  `--matcher_type`, `--range_width`, `--confidence_threshold`,
  `--matches_graph_dot_file`, `--warper_type`, `--finder`, and crop controls.
- The optional `--feature_masks` and `--try_use_gpu` flags.
- CLI troubleshooting for missing files, mask count problems, preview windows,
  and output selection.

## What this sub-skill does not own

- Python `Stitcher` object configuration; use [python-api](../python-api/SKILL.md).
- Verbose file interpretation and match-graph analysis; use
  [diagnostics](../diagnostics/SKILL.md).
- Install/import troubleshooting; use the root [troubleshooting](../../references/troubleshooting.md).

## Start with these bundled files

- [CLI reference](references/cli-reference.md) for verified flags and choices.
- [Workflow recipes](references/workflows.md) for copyable command examples.
- [Troubleshooting](references/troubleshooting.md) for common CLI failures.
- [Validate CLI args](scripts/validate_cli_args.py) when you want a safe
  checker that validates input globs and feature-mask counts without running a
  full stitch.

## Fast routing hints

- Need a single command to stitch a glob of files? Read the workflow recipes.
- Need to check whether a feature-mask list is valid before a full stitch?
  Run the bundled validator.
- Need to interpret dropped images or sparse matches? Route to diagnostics.

## Common success criteria

A good answer from this sub-skill should include:

- The exact `stitch` command or command template.
- The meaning of the relevant flags.
- The expected output file or verbose directory.
- A recovery path if masks, globs, or preview windows fail.
