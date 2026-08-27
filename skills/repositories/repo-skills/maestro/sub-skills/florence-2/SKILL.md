---
name: florence-2
description: "Use Maestro Florence-2 for fine-tuning command/API construction,
  checkpoint load/save, inference, object-detection formatting, LoRA/freeze/none
  choices, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Florence-2 sub-skill

Use this sub-skill when the task is specifically about Maestro's Florence-2 integration: `maestro florence_2 train`, the `maestro.trainer.models.florence_2` Python APIs, Florence-2 checkpoint loading/saving, inference calls, or the Florence object-detection text format.

## Start here

1. Confirm the package and model-specific dependencies are available. For root install and CLI probing guidance, use [installation and CLI](../../references/installation-and-cli.md).
2. Confirm the data layout before building a training command. For JSONL/COCO split rules, Roboflow identifiers, and generic metric details, route to [datasets-and-metrics](../datasets-and-metrics/SKILL.md).
3. Build Florence-2 commands and API calls from [workflows](references/workflows.md) and exact signatures in [API reference](references/api-reference.md).
4. For object detection, use the `<OD>` prefix and the Florence `<loc_*>` suffix rules in [detection formats](references/detection-formats.md).
5. If a CLI/API/data/model issue appears, check [Florence-2 troubleshooting](references/troubleshooting.md) before changing code or broadening dependencies.

## Critical defaults and boundaries

- Default model id: `microsoft/Florence-2-base-ft`.
- Default model revision: `refs/pr/20`.
- Supported Florence-2 optimization strategies are exactly `lora`, `freeze`, and `none`. Do **not** use or recommend `qlora` for Florence-2 in Maestro.
- Florence object detection uses prefix `<OD>` and suffix fragments of the form `class<loc_xmin><loc_ymin><loc_xmax><loc_ymax>` with coordinates normalized to the `0..1000` range.
- This sub-skill owns Florence-specific collate, train, load/save, inference, and formatter decisions. It routes shared dataset validation, Roboflow downloads, COCO/JSONL layout, and metric semantics to [datasets-and-metrics](../datasets-and-metrics/SKILL.md).
- Full fine-tuning or model inference may download Hugging Face model files and usually needs a GPU. The bundled smoke script only checks deterministic text formatting and does not load a model.

## Safe local checks

From the generated Maestro skill tree, run:

```bash
python sub-skills/florence-2/scripts/smoke_florence_detection_format.py --help
python sub-skills/florence-2/scripts/smoke_florence_detection_format.py --json
```

These checks import only Maestro's Florence detection formatter functions and NumPy. They do not open datasets, call Roboflow, contact Hugging Face, download weights, or start training.
