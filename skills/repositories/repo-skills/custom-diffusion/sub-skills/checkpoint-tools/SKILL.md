---
name: checkpoint-tools
description: "Extract, compress, validate, and compose Custom Diffusion checkpoint deltas."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Checkpoint tools

Use this sub-skill for delta and checkpoint math only.

It covers:

- legacy checkpoint delta extraction
- low-rank compression of K/V deltas
- layout validation for extracted, compressed, and composed deltas
- diffusers-side concept composition outputs

It does not cover image generation after composition; route that work to [`../inference/SKILL.md`](../inference/SKILL.md).

## Start here

1. Read [`references/api-reference.md`](references/api-reference.md).
2. Use [`scripts/check_delta_layout.py`](scripts/check_delta_layout.py) before sampling or recompressing.
3. Read [`references/workflows.md`](references/workflows.md) for extraction, compression, and composition order.
4. Check [`references/troubleshooting.md`](references/troubleshooting.md) when a checkpoint family or tensor layout is wrong.

## Safe defaults

- Extraction is CPU-safe and does not delete anything unless `--delete-source` is set.
- Compression and composition are expected to use CUDA and local weights for real runs.
- Layout checks are CPU-safe and do not download models.

Preserve the upstream Adobe Research notice if you edit the bundled helper scripts.
