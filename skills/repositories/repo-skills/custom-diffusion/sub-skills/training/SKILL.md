---
name: training
description: "Guide diffusers Custom Diffusion fine-tuning for single concept,
  multi-concept, prior preservation, modifier tokens, and the SDXL variant."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Training

Use this sub-skill when you need to fine-tune Custom Diffusion with the diffusers training entry points.

It covers:

- single-concept and multi-concept training
- generated or real prior preservation
- modifier tokens and initializer tokens
- cross-attention freeze choices
- SDXL training and checkpoint output planning

It does not cover the legacy Stable Diffusion checkout path. Route those tasks to the diffusers-side route and treat the legacy checkout files as reference-only or excluded.

## Start here

1. Read [`references/workflows.md`](references/workflows.md).
2. Read [`references/cli-reference.md`](references/cli-reference.md).
3. Read [`references/data-formats.md`](references/data-formats.md).
4. Run [`scripts/validate_training_inputs.py`](scripts/validate_training_inputs.py) before an expensive launch.
5. Check [`references/troubleshooting.md`](references/troubleshooting.md) when the run fails or stalls.

## Route onward

- Use [`../data-preparation/SKILL.md`](../data-preparation/SKILL.md) first when the concept data or prior bundle is not ready.
- Use [`../inference/SKILL.md`](../inference/SKILL.md) after a successful training run when you want to sample the result.
- Use [`../checkpoint-tools/SKILL.md`](../checkpoint-tools/SKILL.md) when you need to extract, compress, or compose the delta outputs.

## Runtime notes

- The default path updates K/V cross-attention only.
- `crossattn` updates all cross-attention weights.
- SDXL uses a dual-text-encoder path and a larger default resolution.
- CUDA is required for truthful training guidance.
