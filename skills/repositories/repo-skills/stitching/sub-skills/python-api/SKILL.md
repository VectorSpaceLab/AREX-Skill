---
name: python-api
description: "Routes programmatic use of `Stitcher`, `AffineStitcher`, image
  lists, feature masks, component settings, and API-default inspection for the
  stitching package."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Python API

Use this sub-skill when the user wants to call the package from Python instead
of the shell.

## Typical triggers

- "How do I use `Stitcher`?"
- "I want to stitch loaded NumPy arrays instead of filenames."
- "How do I make an affine panorama?"
- "What are the default settings?"
- "How do I pass masks or tune matching in code?"

## What this sub-skill owns

- `from stitching import Stitcher, AffineStitcher`
- `Stitcher.DEFAULT_SETTINGS` and `AffineStitcher.AFFINE_DEFAULTS`
- `Images.of` and the filename-vs-NumPy input split
- Feature detection/matching defaults and tuning knobs
- Camera, warper, cropper, seam-finder, blender, and timelapse options
- `StitchingError` and `StitchingWarning` patterns that a caller should handle

## What this sub-skill does not own

- Shell command building; use [cli](../cli/SKILL.md).
- Verbose file interpretation and matches-graph analysis; use
  [diagnostics](../diagnostics/SKILL.md).
- Install/import setup; use the root [installation notes](../../references/installation.md).

## Start with these bundled files

- [API reference](references/api-reference.md) for verified signatures and
  choices.
- [Workflow recipes](references/workflows.md) for copyable Python snippets.
- [Troubleshooting](references/troubleshooting.md) for common mistakes and
  recovery steps.
- [Inspect defaults helper](scripts/inspect_stitching_defaults.py) to print a
  JSON summary of installed defaults and signatures.

## Fast routing hints

- If the prompt names `Stitcher`, `AffineStitcher`, or `Images.of`, read the
  API reference first.
- If the prompt asks for the closest Python equivalent to a CLI command, use
  the workflow recipes.
- If the prompt is about dropped images or mask mismatches, hand off to
  diagnostics.

## Common success criteria

A good answer from this sub-skill should include:

- Exact signatures or settings names when relevant.
- A concrete Python snippet that works with filenames or loaded arrays.
- The expected output file or return value shape.
- A clear error-handling or warning-handling path for invalid inputs.
