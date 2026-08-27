---
name: model-api
description: "Use OmegaFold programmatically: configs, model construction,
  forward inputs and outputs, confidence helpers, architecture choices, and API
  debugging."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OmegaFold Model API

Use this sub-skill when an agent needs to call OmegaFold from Python, inspect its model/config API, load weights manually, or diagnose backend and dependency failures. For end-user command recipes, use [inference CLI](../inference-cli/SKILL.md). For FASTA normalization, generated input tensors, and PDB output details, use [data and outputs](../data-and-outputs/SKILL.md).

## Quick Routes

- Inspect installed API safely with [`scripts/inspect_model_api.py`](scripts/inspect_model_api.py); it imports OmegaFold, prints signatures/config summaries, and avoids downloads.
- Build configs and call the model with [`references/api-reference.md`](references/api-reference.md).
- Understand model 1 vs model 2 and major modules with [`references/model-architecture.md`](references/model-architecture.md).
- Debug invalid model ids, state-dict mismatches, NumPy/Torch/CUDA/MPS issues, and API OOM with [`references/troubleshooting.md`](references/troubleshooting.md).

## Programmatic Inference Shape

A safe custom API flow is: create `cfg = omegafold.make_config(1 or 2)`, instantiate `omegafold.OmegaFold(cfg)`, load a matching state dict, move to a real device, prepare inputs through `omegafold.pipeline.fasta2inputs`, call `model(input_data, predict_with_confidence=True, fwd_cfg=forward_config)`, then write PDBs through the data/output sub-skill.

Do not present OmegaFold as a training or fine-tuning toolkit. This release is inference code; unsupported training loops, gradient recipes, optimizer setup, or model surgery are outside this sub-skill.
