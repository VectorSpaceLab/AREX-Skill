---
name: rayorch-acceleration
description: "Accelerate DataFlow operators with RayOrch while preserving
  compile semantics, storage behavior, CPU fallback, deterministic ordering, and
  actor cleanup."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# RayOrch acceleration

Use this sub-skill when you want to wrap an existing DataFlow operator in RayOrch and keep the surrounding pipeline behavior unchanged.

## Covers
- `RayAcceleratedOperator`
- `.op_cls_init(...)` and wrapped operator constructor args
- `replicas`, `num_gpus_per_replica`, and optional `env`
- normal, batched, and stream-batched pipelines
- CPU fallback, fractional GPU allocation, deterministic ordering, and actor cleanup

## Keep unchanged
- compile-time key validation
- storage selection and cache layout
- operator authoring and backend choice

## Route elsewhere
- operator authoring, storage classes, or `input_*` / `output_*` validation -> [`pipeline-foundations`](../pipeline-foundations/SKILL.md)
- serving backend choice or local model selection -> [`serving-cli`](../serving-cli/SKILL.md) or the workflow owner

## Read first
- `references/api-reference.md`
- `references/workflows.md`
- `references/troubleshooting.md`
- `scripts/smoke_rayorch_cpu.py`

## Rules of thumb
1. Wrap only row-independent, deterministic operators.
2. Use `num_gpus_per_replica=0.0` for CPU-only smoke and fallback.
3. Make fractional GPU allocation explicit when sharing devices.
4. Call `shutdown()` when you manage Ray stages manually; compiled pipelines auto-shutdown after each stage.
5. Keep outer storage as the normal DataFlow storage; the Ray layer only accelerates execution.

If a request needs operator schema changes or key validation help, hand it off to pipeline-foundations before touching RayOrch.
