---
name: custom-diffusion
description: "Route Custom Diffusion workflows for concept data prep, diffusers
  training and SDXL, sample generation, delta tools, and CustomConcept101
  evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Custom Diffusion

Use this repo skill for the diffusers-side Custom Diffusion workflow family:

- prepare concept data and real-prior bundles
- train single- and multi-concept models with diffusers or SDXL
- sample from delta checkpoints
- extract, compress, and compose delta artifacts
- evaluate generated samples on CustomConcept101

## Start here

1. Read `references/repo-provenance.md` to confirm the source baseline.
2. Read `references/workflows.md` for the route map.
3. Run `scripts/check_runtime.py --require-cuda` to confirm the CUDA/import stack.
4. Use `scripts/validate_concepts.py` when a concept-list JSON needs a structural check.
5. Open the focused sub-skill for the task family you have.

## Routes

### `data-preparation`
Use when you need instance images, real-prior image lists, caption files, or concept JSON for training.
Start with [`sub-skills/data-preparation/SKILL.md`](sub-skills/data-preparation/SKILL.md).

### `training`
Use when you need diffusers training, SDXL training, prior preservation, modifier tokens, or checkpoint output planning.
Start with [`sub-skills/training/SKILL.md`](sub-skills/training/SKILL.md).

### `inference`
Use when you need to load a Custom Diffusion delta and generate samples from prompts or prompt files.
Start with [`sub-skills/inference/SKILL.md`](sub-skills/inference/SKILL.md).

### `checkpoint-tools`
Use when you need delta extraction, compression, or composition.
Start with [`sub-skills/checkpoint-tools/SKILL.md`](sub-skills/checkpoint-tools/SKILL.md).

### `benchmarking`
Use when you need to score generated images with CustomConcept101 CLIP/DINO evaluation.
Start with [`sub-skills/benchmarking/SKILL.md`](sub-skills/benchmarking/SKILL.md).

## Install and runtime notes

- Use Python 3.11 or newer.
- Install a CUDA-enabled PyTorch/torchvision pair before the diffusers workflows.
- Verified public stack: `diffusers==0.21.4`, `accelerate==0.24.1`, `transformers==4.31.0`, `clip-retrieval==2.45.0`, `pandas`, `scipy`, `scikit-learn`, `tqdm`.
- Optional workflow extras: `xformers`, `bitsandbytes`, `deepspeed`, `modelcards`.
- The source training, sampling, compression, composition, and evaluation flows are CUDA-backed; the delta extraction route is the only selected CPU-substitutable workflow.
- Legacy checkout-based Stable Diffusion scripts are treated as reference-only or excluded in this generated skill.

## Minimal smoke check

After installing the stack, run:

```bash
python scripts/check_runtime.py --require-cuda
```

If you are only checking importability, omit `--require-cuda`.
