---
name: model-zoo-and-converters
description: "Route detrex model zoo selection, pretrained backbones, and safe
  checkpoint conversion."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# model-zoo-and-converters

Use this sub-skill when you need to:
- choose the right detrex project family or pretrained variant;
- decide whether a model zoo row is a converted checkpoint, a hacked-trainer run, or a standard detrex config;
- inspect a checkpoint before converting it;
- convert an official DETR-family checkpoint into detrex format;
- route DINO, MaskDINO, and CO-MOT work to the right project notes.

## Read in this order
1. [Project guide](references/project-guide.md) to identify the family and trainer/config route.
2. [Converters](references/converters.md) if the checkpoint needs key remapping or class-head reshaping.
3. [Backbones](references/backbones.md) if the problem is pretrained backbone selection or shape compatibility.
4. [Troubleshooting](references/troubleshooting.md) for mismatch, head-shape, or missing-key failures.
5. [Checkpoint tools](scripts/checkpoint_tools.py) to inspect first, then run a bounded local conversion.

## Guardrails
- Prefer inspect mode before conversion.
- Keep conversions local; do not fetch checkpoints in this skill.
- If a checkpoint already looks detrex-shaped, do not reconvert it.
- If the family is not one of the bundled converter modes, stop and route to the closest project reference.
