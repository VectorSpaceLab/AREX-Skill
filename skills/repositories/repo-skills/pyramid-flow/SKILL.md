---
name: pyramid-flow
description: "Use Pyramid-Flow for video generation, data precomputation, Causal
  Video VAE, distributed training, and reusable model-component inspection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Pyramid-Flow

Use this skill when a task names Pyramid-Flow, `pyramid-flow`, `PyramidDiTForVideoGeneration`, `CausalVideoVAE`, the generation demos, the annotation/precompute helpers, or the training launchers in this repository.

## Route by task

- **Model APIs, schedulers, VAE encode/decode, and distributed helpers**: read `sub-skills/core-components/SKILL.md`.
- **Prompt/image generation, Gradio demos, multi-GPU inference, and checkpoint selection**: read `sub-skills/generation-inference/SKILL.md`.
- **JSONL annotations, dataset loading, text-feature extraction, and VAE-latent precompute**: read `sub-skills/data-preparation/SKILL.md`.
- **AR/non-AR DiT fine-tuning, Causal VAE training, and launch-time prerequisites**: read `sub-skills/training-workflows/SKILL.md`.

## Start here

- `references/model-overview.md` for the model families and workflow map.
- `references/installation.md` for import-root and dependency setup.
- `references/troubleshooting.md` for cross-cutting install, backend, checkpoint, and routing failures.
- `references/repo-provenance.md` for the source snapshot used to build this skill.
- `references/repo-routing-metadata.json` for managed router placement metadata.
- `scripts/check_environment.py` for a safe environment and bundled-helper smoke check.

## Quick smoke

From a Pyramid-Flow checkout or a shell that can point to one, run:

```bash
python scripts/check_environment.py --repo PATH_TO_PYRAMID_FLOW
```

Use `--json` for machine-readable output. The helper checks the common runtime imports, CUDA visibility when torch is available, and the bundled helper script entry points without starting generation or training.

## Installation and runtime baseline

- The repository snapshot has no `pyproject.toml` or `setup.py`; make the checkout root importable with `PYTHONPATH` or by running from the checkout root.
- Install the repo's runtime dependencies before trying any workflow that imports `torch`, `diffusers`, `transformers`, `accelerate`, `sentencepiece`, `jsonlines`, `cv2`, or the training/data helpers.
- Keep checkpoint downloads, model-cache creation, feature extraction, and training launches explicit. The bundled helpers only plan or preflight those workflows unless you ask them to execute.
- Treat CUDA as required for truthful generation and training. CPU is useful for bounded import, syntax, fixture, and scheduler checks only.

## Safety defaults

- Do not assume the repo checkout is installed as a package; top-level imports come from the repository root.
- Do not launch generation, extraction, or training until the matching sub-skill preflight passes and the needed checkpoint or dataset artifacts are present.
- Do not route a task to a narrower sub-skill if the user is actually asking about the overall repo layout, repo routing metadata, or a cross-cutting environment issue.
- Do not rely on the original checkout remaining available after skill generation; the sub-skills and bundled references are the persistent operating knowledge.
