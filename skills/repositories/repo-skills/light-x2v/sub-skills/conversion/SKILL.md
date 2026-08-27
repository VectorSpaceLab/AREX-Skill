---
name: "conversion"
description: "Routes LightX2V LoRA extraction, LoRA merging, dummy-meta export,
  and weight-format conversion preparation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Conversion

Use this sub-skill for checkpoint surgery, LoRA preparation, dummy-meta export, and other weight-preparation workflows that sit beside the main generation stack.

## Typical triggers

- "extract a LoRA from two checkpoints"
- "merge LoRA weights into a base model"
- "export dummy-meta safetensors"
- "how do I convert or quantize weights?"
- "what are the LoRA key conventions?"

## Read first

- [`references/formats.md`](references/formats.md) for the weight-format and LoRA naming conventions.
- [`references/workflows.md`](references/workflows.md) for the common conversion and preparation flows.
- [`references/troubleshooting.md`](references/troubleshooting.md) for CUDA extension, key-mapping, and shape-mismatch failures.
- [`../../references/troubleshooting.md`](../../references/troubleshooting.md) for cross-cutting package and environment failures.

## What belongs here

Include:
- LoRA extraction from a source / target checkpoint pair
- LoRA merging back into a base checkpoint
- dummy-meta safetensors export
- weight-format and metadata preparation for LightX2V deployment
- quantization planning and conversion guidance when the tooling is light enough to document safely

Exclude or route elsewhere:
- direct generation → `sub-skills/inference/`
- HTTP server and queue management → `sub-skills/serving/`
- controller / encoder / transformer / decoder deployment → `sub-skills/disagg/`
- training workflows → out of scope for this skill graph

## Bundled helpers

- [`scripts/extract_lora.py`](scripts/extract_lora.py)
- [`scripts/merge_lora.py`](scripts/merge_lora.py)
- [`scripts/export_dummy_meta.py`](scripts/export_dummy_meta.py)

The full conversion utility is documented in the references but is intentionally left reference-only because it depends on heavier optional CUDA extension build paths and broad model-family branches.

## Safe starting checks

- `python scripts/check_install.py`
- `python sub-skills/conversion/scripts/export_dummy_meta.py --help`
- `python sub-skills/conversion/scripts/extract_lora.py --help`
- `python sub-skills/conversion/scripts/merge_lora.py --help`

## Guidance style

When you answer from this route, name:
- the source and target checkpoint layout
- the LoRA format or diff format involved
- whether the user wants extraction, merging, or metadata-only export
- whether the full converter is actually needed or a lightweight helper is enough
- the build prerequisites if quantization or CUDA extensions are involved

## Decision points

When routing a weight-preparation request, choose the narrowest safe helper:
- metadata only → `export_dummy_meta.py`
- source/target delta extraction → `extract_lora.py`
- applying an extracted or diff-style LoRA back into a base checkpoint → `merge_lora.py`
- broader architecture conversion or quantization planning → reference the full converter, but keep it reference-only unless the user explicitly needs that heavier path

Common reminders:
- `safetensors` and `pytorch` are the two supported source formats in the bundled helpers
- LoRA suffixes vary by model family, so mention the expected naming convention when the user asks about missing keys
- `--diff-only` is the safest answer when the user only needs raw deltas
- the dummy-meta helper is useful when the config only needs tensor metadata and not the full payload
- the full converter depends on heavier optional CUDA extension build paths, so it stays out of the bundled runtime surface for now

If a request is really about runtime generation or serving, route away from this sub-skill rather than forcing it into conversion language.
