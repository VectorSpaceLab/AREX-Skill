---
name: core-apis
description: "Use and debug EasyR1 DataProto, core algorithm, dynamic batching,
  logger, and support utility APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# EasyR1 Core APIs

Use this sub-skill when a task needs EasyR1's low-level support APIs rather than a full training launch or checkpoint conversion workflow.

## Read first

- [references/api-reference.md](references/api-reference.md): API shapes, signatures, batching semantics, algorithm/loss helpers, dynamic batching, logger/tracker helpers, and checkpoint utility relationships.
- [references/troubleshooting.md](references/troubleshooting.md): fixes for DataProto construction and union errors, chunk/padding mismatches, GRPO grouped-rollout assertions, mask/shape failures, dynamic batching restore mistakes, logger setup issues, and backend limitations.
- [scripts/easyr1_dataproto_smoke.py](scripts/easyr1_dataproto_smoke.py): deterministic CPU smoke check for DataProto split/concat/pad/unpad/repeat, dynamic batching restore, and tiny KL/policy-loss sanity checks.

## Routing boundaries

- Use this sub-skill for `DataProto`, `DataProtoItem`, `DataProtoFuture`, tensor/non-tensor batches, padding helpers, `batch_collate`, core advantage/KL/loss helpers, dynamic sequence-length batching, and logging/tracking support helpers.
- Route training configuration, Ray/vLLM/FSDP launch commands, algorithm override recipes, and full training runtime decisions to the training-workflows sub-skill.
- Route model checkpoint merge/export, Hugging Face conversion, shard inspection, and LoRA merge behavior to the checkpoint-export sub-skill.
- CPU/API checks here do not prove full EasyR1 training readiness; full training still needs a CUDA-oriented EasyR1 runtime with the appropriate flash-attn, vLLM, Ray, model, and dataset stack.

## Quick validation

Run the bundled smoke after the EasyR1 package and its CPU API dependencies are importable. From this sub-skill directory:

```bash
python scripts/easyr1_dataproto_smoke.py
```

Expected final line:

```text
easy-r1 core API smoke: success
```
