---
name: model-architecture
description: "Inspect and configure HRM ACT v1 model internals, losses,
  FlashAttention layers, and dynamic model identifiers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# HRM Model Architecture

Use this sub-skill when the task is to understand, configure, inspect, or debug
the Hierarchical Reasoning Model (HRM) ACT v1 implementation rather than to run
full training.

## When to use

- The user asks about HRM high-level/low-level recurrent modules, ACT halting,
  Q heads, carry state, sparse puzzle embeddings, StableMax loss, or
  FlashAttention-backed attention blocks.
- A config mentions `arch.name=hrm.hrm_act_v1@HierarchicalReasoningModel_ACTV1`
  or `arch.loss.name=losses@ACTLossHead`.
- A model import fails because `flash_attn`, `flash_attn_interface`,
  `adam_atan2_backend`, CUDA, or dynamic `module@class` identifiers are wrong.
- The user needs to alter hidden size, heads, cycles, layers, positional
  encodings, halt steps, or loss type safely.

## Route map

1. Read [references/architecture.md](references/architecture.md) for the HRM
   ACT v1 object graph, carry objects, input/output tensors, and halting
   mechanics.
2. Read [references/api-reference.md](references/api-reference.md) for verified
   config fields, function/class signatures, losses, and dynamic identifier
   rules.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for
   import/backend/config errors.
4. Run [scripts/inspect_model_config.py](scripts/inspect_model_config.py) to
   inspect identifiers and optionally run CUDA dependency smokes from an HRM
   checkout.

## Critical facts

- The default architecture config uses
  `hrm.hrm_act_v1@HierarchicalReasoningModel_ACTV1` wrapped by
  `losses@ACTLossHead` with `loss_type=stablemax_cross_entropy`.
- `models/layers.py` imports FlashAttention at module import time. If neither
  `flash_attn_interface` nor `flash_attn` is importable, HRM model imports fail.
- `pretrain.py` imports `AdamATan2` from `adam_atan2`; real training requires
  the compiled `adam_atan2_backend` CUDA extension.
- Real model construction and forward execution are CUDA-oriented. CPU imports
  and source inspection are useful for config facts but do not verify the
  required training/evaluation backend.
- The repository's tiny model smoke under current dependency versions exposed a
  runtime issue where FlashAttention output may be non-contiguous and
  `models/layers.py` calls `.view(...)`; use this as troubleshooting evidence
  if a forward pass fails with a stride/view error.

## Boundaries

- This sub-skill owns model/loss/config/API understanding and environment
  smokes for model dependencies.
- Use `data-preparation` for dataset schema, builders, and visualization.
- Use `training-evaluation` for Hydra training commands, checkpoint evaluation,
  W&B, and ARC post-processing.
- Do not present a CPU import as proof that HRM can train or evaluate. The
  backend gate is CUDA + FlashAttention + adam-atan2 backend.

## Bounded inspection

From an HRM checkout, run:

```bash
python <skill>/sub-skills/model-architecture/scripts/inspect_model_config.py \
  --repo-root /path/to/HRM --json
```

If a CUDA environment is prepared and the user wants dependency readiness:

```bash
python <skill>/sub-skills/model-architecture/scripts/inspect_model_config.py \
  --repo-root /path/to/HRM --cuda-smoke
```

The helper verifies imports and dependency smokes. It intentionally avoids long
training and does not require real datasets or checkpoints.
