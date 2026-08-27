---
name: inference
description: "Load Donut checkpoints, build prompts, run single-image inference,
  convert JSON tokens, and launch the Gradio demo."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Inference

Use this sub-skill for one-image Donut inference, prompt selection, JSON token round-trips, and the Gradio demo.

## Route First

- Start with [`references/demo-and-prediction.md`](references/demo-and-prediction.md) for command recipes, prompt templates, image preprocessing behavior, output shapes, and token round-trips.
- Use [`scripts/run_inference.py`](scripts/run_inference.py) for CLI inference and prompt-variant comparison.
- Use [`scripts/launch_demo.py`](scripts/launch_demo.py) for the Gradio demo launcher.
- Use [`references/troubleshooting.md`](references/troubleshooting.md) for model loading, download, prompt-token, CPU/CUDA, and Gradio failures.
- If you need dataset scoring, accuracy, or evaluation over a dataset, route to [`../training/SKILL.md`](../training/SKILL.md).
- If the image came from synthetic generation and the user is actually asking about synthetic-data creation, route to [`../synthdog/SKILL.md`](../synthdog/SKILL.md) instead.
- For the shared package API and cross-cutting troubleshooting, use the parent-tree references (`../../references/api-reference.md` and `../../references/troubleshooting.md`) once the root skill is in place.

## Boundaries

- Include: `DonutConfig`, `DonutModel`, `from_pretrained`, `inference`, `json2token`, `token2json`, prompt/task selection, image preprocessing behavior, CPU/CUDA inference behavior, demo launcher.
- Exclude: training loops, Lightning trainer setup, dataset evaluation metrics, SynthDoG generation.

## Quick Paths

- `python scripts/run_inference.py --help`
- `python scripts/launch_demo.py --help`

## What to do

- Load a local checkpoint or Hub checkpoint with the Donut runtime API.
- Build the exact task prompt the checkpoint expects.
- Run one image at a time, or compare several prompt variants against the same image.
- Convert structured JSON to Donut tokens and back when you need to inspect prompt/output formatting.
- Start the Gradio demo with a local model and a sample image if available.
