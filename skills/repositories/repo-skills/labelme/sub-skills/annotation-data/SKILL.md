---
name: annotation-data
description: "Helps read, validate, summarize, repair, and generate labelme
  Annotation Files, Shapes, Flags, groups, and mask data without relying on
  unstable labelme internals."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Annotation Data

Use this route when the task is about labelme JSON Annotation Files,
Shape/Flag/Group semantics, mask rasterization, image-data round trips, or safe
headless validation of existing annotations.

## Workflow

1. Read [`references/data-formats.md`](references/data-formats.md) for the
   semantic model and file layout.
2. Use [`scripts/validate_labelme_json.py`](scripts/validate_labelme_json.py) to
   validate or summarize a JSON file before touching conversion code or
   downstream dataset consumers.
3. Use the [`shared JSON helper`](../../scripts/labelme_json_core.py) as the
   self-contained parser/rasterizer when working outside the GUI.
4. When the task is to recover from a malformed annotation file, read
   [`references/troubleshooting.md`](references/troubleshooting.md) first so you
   know which errors are repairable and which ones indicate missing image data
   or invalid Shape fields.
5. For public API details and exact signatures, prefer the installed package
   inspection evidence in [`references/api-reference.md`](references/api-reference.md)
   over source guesses.

## What this route covers

- One Image per Annotation File.
- Image-level Flags and per-Shape Flags.
- `shape_type` handling for polygon, rectangle, circle, line, linestrip,
  oriented_rectangle, point, points, and mask.
- Embedded `imageData` versus external `imagePath`.
- Windows-path normalization during load.
- `imageHeight` / `imageWidth` consistency checks.
- Mask Shape bbox clipping and canvas placement.
- Shape grouping through `group_id`.
- Lossless round-trips for extra top-level keys when they are not reserved.

## What this route does not cover

- Launching the GUI or choosing CLI flags: use
  [`../cli-and-config/SKILL.md`](../cli-and-config/SKILL.md).
- Converting annotations to training artifacts: use
  [`../dataset-export/SKILL.md`](../dataset-export/SKILL.md).
- AI-assisted prompting or model compatibility: use
  [`../ai-assisted-annotation/SKILL.md`](../ai-assisted-annotation/SKILL.md).
- Source/repo maintenance: use
  [`../repo-development/SKILL.md`](../repo-development/SKILL.md).

## Practical checks

- `scripts/validate_labelme_json.py file.json` applies the current codec
  invariants (required `shape_type`, shape-specific point counts, finite
  coordinates, flags, groups, and mask dimensionality) and reports unknown
  labels when a vocabulary is supplied.
- `scripts/validate_labelme_json.py --json file.json` produces machine-readable
  summaries for downstream automation.
- `--allow-missing-image-file` relaxes only external-image resolution when
  `imageData` is null; it does not skip JSON or Shape validation.
- Keep downstream dataset code headless: labelme JSON parsing does not require
  Qt or a display.

## References

- Read [`references/data-formats.md`](references/data-formats.md) for the data
  model and file fields.
- Read [`references/api-reference.md`](references/api-reference.md) for verified
  signatures and object shapes.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for
  malformed file recovery and mask-related edge cases.
