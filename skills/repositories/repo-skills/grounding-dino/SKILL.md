---
name: grounding-dino
description: "Use GroundingDINO for open-vocabulary object detection,
  single-image inference, COCO evaluation, pseudo-label dataset creation, and
  safe web or downstream integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# GroundingDINO Repo Skill

Use this repo skill when a user asks about the `groundingdino` Python package, GroundingDINO open-set object detection, Grounding DINO config/checkpoint workflows, or the original demo capabilities from the IDEA-Research GroundingDINO project.

## Choose A Route

- `sub-skills/inference/`: single-image CLI/API inference, `load_model`, `load_image`, `predict`, `annotate`, the `Model` wrapper, class-list prompts, token spans, thresholds, devices, and output boxes.
- `sub-skills/evaluation/`: COCO-style zero-shot AP evaluation, category-prompt construction, `CocoGroundingEvaluator`, `pycocotools`, benchmark caveats, and low-AP diagnosis.
- `sub-skills/dataset-annotation/`: pseudo-label an image folder, draw review images, export COCO-format data, and manage optional FiftyOne workflow dependencies.
- `sub-skills/integrations/`: Gradio apps, Hugging Face checkpoint UX, Grounded-SAM/SAM handoffs, Stable Diffusion or GLIGEN notebook-style integrations, and color/box contracts.

## Quick Install Check

GroundingDINO is a PyTorch package named `groundingdino`. A minimal install typically needs:

```bash
pip install -e .
```

For a reusable project or app, verify the installed package before running model code:

```bash
python scripts/check_grounding_dino_install.py
```

Read `references/install-and-models.md` before changing dependencies, compiling custom ops, selecting a config/checkpoint pair, or interpreting CPU-only warnings.

## Core Facts

- The packaged model configs are `GroundingDINO_SwinT_OGC.py` and `GroundingDINO_SwinB_cfg.py`; both use `modelname="groundingdino"`, `num_queries=900`, `max_text_len=256`, and `bert-base-uncased` text encoding.
- Released workflows require a config file and a matching checkpoint file; this skill does not download checkpoints unless an integration helper explicitly receives Hugging Face download arguments.
- The public inference API returns normalized `cxcywh` boxes, logits/confidence scores, and phrases; annotation helpers convert boxes for visualization.
- Training code is not part of this repo skill because the source README lists training-code release as incomplete.

## Shared References

- `references/api-overview.md`: package modules, public API surfaces, and where detailed signatures live.
- `references/install-and-models.md`: install/build behavior, dependencies, model variants, checkpoints, and device guidance.
- `references/prompt-and-threshold-guide.md`: prompt punctuation, class lists, thresholds, token spans, and no-detection diagnosis.
- `references/troubleshooting.md`: cross-cutting install, import, model, data, device, and workflow failures.
- `references/repo-provenance.md`: source commit, dirty-state baseline, package version, and evidence paths.
- `references/repo-routing-metadata.json`: structured DisCo router metadata used during managed import.
