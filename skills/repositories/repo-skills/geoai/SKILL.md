---
name: geoai
description: "Route GeoAI geospatial data, inference, training,
  foundation-model, and integration workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# GeoAI

Use this repo skill when the task is about GeoAI: geospatial data inspection and downloads, raster/vector conversion, batch pipelines, model inference, training and fine-tuning, foundation models and embeddings, or the QGIS/MCP/agent integration surfaces.

GeoAI has a broad package surface. Start with the smallest sub-skill that matches the user's intent, then read the linked references for the exact APIs, commands, and failure modes.

## First steps

1. Read [installation and environment](references/installation-and-environment.md) to choose the right install path and optional extras.
2. Run [scripts/check_geoai_env.py](scripts/check_geoai_env.py) for a safe import/CLI/backend smoke check when you need to confirm the environment before deeper work.
3. Read [top-level API map](references/top-level-api-map.md) when you need to see which module family owns a symbol.
4. Read [troubleshooting](references/troubleshooting.md) for cross-cutting install/import/CLI/backend issues.
5. Read [repository provenance](references/repo-provenance.md) if you need to confirm whether this skill still matches the checkout you have.

## Route by task

| User request | Read next |
| --- | --- |
| Inspect raster/vector files, validate CRS/bounds, download STAC/NAIP/Overture data, run `geoai pipeline`, tile or vectorize data | [Geospatial data pipelines](sub-skills/geospatial-data-pipelines/SKILL.md) |
| Run segmentation, detection, prompt-based segmentation, RF-DETR, water/cloud/super-resolution, ONNX, or HF-style inference | [Detection and segmentation inference](sub-skills/detection-segmentation-inference/SKILL.md) |
| Prepare training layouts, fit/fine-tune models, inspect losses or metrics, or publish checkpoints carefully | [Training and finetuning](sub-skills/training-and-finetuning/SKILL.md) |
| Query the foundation-model registry, work with embeddings, DINOv3, Prithvi, UniverSat, TESSERA, Moondream, vLLM, or captioning | [Foundation models, embeddings, and VLMs](sub-skills/foundation-models-embeddings-vlms/SKILL.md) |
| Configure the QGIS plugin, the GeoAI MCP server, or optional Strands agent integrations | [GeoAI integrations, agents, QGIS, and MCP](sub-skills/integrations-agents-qgis-mcp/SKILL.md) |

## Package identity

- Distribution name: `geoai-py`
- Import name: `geoai`
- Console entry point: `geoai`
- Public Python support: Python 3.12 or newer

## Safe install pattern

- For normal use, install the published package: `pip install geoai-py`.
- When working from a local checkout, an editable install is reasonable: `pip install -e .`.
- Install optional extras only when the task needs them. The main extras currently include `agents`, `building`, `networks`, `onnx`, `osd`, `rfdetr`, `sr`, `terratorch`, and `vllm`.
- Do not install optional extras just because they exist; route to the sub-skill that owns the workflow first.

## Minimal smoke check

A quick package smoke check should be enough before deeper work:

```bash
python -c "import geoai; print(geoai.__version__)"
python -m geoai.cli --help
```

If the user needs backend confirmation for GPU workflows, use the bundled smoke script rather than jumping straight to a heavy model run.

## What this root skill does not do

- It does not perform downstream geospatial analysis or model execution by itself.
- It does not tell future agents to open files from the original repository checkout when a bundled skill reference or script exists.
- It does not bundle training, inference, or integration details that belong in the sub-skills.

## Follow-up references

- Use [repository provenance](references/repo-provenance.md) to check staleness before refresh.
- Use [top-level API map](references/top-level-api-map.md) to trace a public symbol to the owning sub-skill.
- Use [troubleshooting](references/troubleshooting.md) for cross-cutting error recovery before reading the more specialized sub-skill troubleshooting file.
