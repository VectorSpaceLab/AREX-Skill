---
name: "alpamayo-r1"
description: "Router for Alpamayo R1 multimodal driving inference and trajectory sampling."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Alpamayo R1

Use this skill for Alpamayo R1 inference on PhysicalAI-AV clips: load one clip, build the multimodal prompt, run the model on CUDA, inspect reasoning traces, and compare predicted trajectories to ground truth.

## When to use this skill

- The user wants to run Alpamayo R1 on a PhysicalAI-AV clip.
- The user asks how to load the dataset, build the chat template, or sample future trajectories.
- The user wants Chain-of-Causation text, minADE comparison, or notebook-style visualization.
- The user needs help with gated HF resources, CUDA setup, or flash-attn / SDPA fallback behavior.

## Install and verify

Use a Python 3.12 CUDA environment with the package dependencies installed, then perform a minimal import check from outside the checkout:

```bash
python -m pip install -e <repo-checkout>
python -I -c "import alpamayo_r1, torch; print(alpamayo_r1.__name__); print(torch.cuda.is_available())"
```

If the editable install or import fails, open `references/troubleshooting.md` before changing the workflow.

## Route map

- `sub-skills/inference/SKILL.md` — the end-to-end driving inference workflow, including dataset loading, prompt creation, model sampling, output interpretation, and the bundled smoke script.
- `references/repo-provenance.md` — source commit, version, and evidence paths used to build this skill.
- `references/repo-routing-metadata.json` — structured router metadata consumed during repo-skill import.
- `references/troubleshooting.md` — cross-cutting install/import/backend guidance.

## Shared notes

- This repository exposes no public CLI entry point; use the Python API or the bundled smoke script from the inference sub-skill.
- The primary workflow is CUDA-first. Flash-attn is the default attention path, but the inference sub-skill documents the SDPA fallback for compatibility issues.
- Training, SFT, and RL post-training are out of scope for this skill.

## Fastest path

1. Read `sub-skills/inference/SKILL.md`.
2. Use `sub-skills/inference/scripts/run_inference_smoke.py` for a runnable sample.
3. If anything fails before the first clip loads, check `references/troubleshooting.md`.
