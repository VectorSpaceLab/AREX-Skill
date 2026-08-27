---
name: diagnostics
description: "Routes verbose panorama diagnosis, matches-graph inspection, crop
  and seam troubleshooting, feature-mask recovery, and sample-image workflows
  for the stitching package."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Diagnostics

Use this sub-skill when stitching is failing or the output looks wrong and you
need to find which stage of the pipeline caused the problem.

## Typical triggers

- "Why did one image disappear from the panorama?"
- "How do I inspect the matches graph?"
- "The cropper failed or returned a strange border"
- "I need to debug feature masks or timelapse outputs"
- "I want to reproduce the repository's verbose outputs"

## What this sub-skill owns

- `stitch_verbose(...)` and its step-by-step output directory.
- Matches-graph inspection and dropped-image diagnosis.
- Feature-mask mismatch troubleshooting.
- Crop, seam, and timelapse failure analysis.
- `confidence_threshold`, detector choice, and `range_width` recovery hints.
- Optional sample-image downloads for reproducing public native workflows.

## What this sub-skill does not own

- Shell command construction; use [cli](../cli/SKILL.md).
- Core Python API signatures; use [python-api](../python-api/SKILL.md).
- Install/import failures; use the root [troubleshooting](../../references/troubleshooting.md).

## Start with these bundled files

- [Diagnostic workflows](references/diagnostic-workflows.md) for ordered
  recovery playbooks.
- [Troubleshooting](references/troubleshooting.md) for symptoms and fixes.
- [Inspect verbose dir](scripts/inspect_verbose_dir.py) when you already have a
  verbose output directory and want to summarize likely pipeline failures.
- [Sample image downloader](../../scripts/download_sample_images.py) when you
  need the public fixtures used by the repository's native tests.

## Fast routing hints

- If the failure is about dropped images or low match confidence, inspect the
  matches graph first.
- If the failure is about masks, check mask dimensions and list length before
  rerunning the stitch.
- If crop fails, treat `--no-crop` or `crop=False` as the safest recovery.

## Common success criteria

A good answer from this sub-skill should include:

- The likely failed stage.
- A concrete next diagnostic command or file to inspect.
- A specific recovery action.
- An explanation of any missing fixtures or headless limitations.
