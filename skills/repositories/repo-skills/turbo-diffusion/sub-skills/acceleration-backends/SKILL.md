---
name: acceleration-backends
description: "Diagnose and choose TurboDiffusion CUDA custom-op, INT8/FastNorm,
  SLA, and SageSLA acceleration backends."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Acceleration Backends

Use this sub-skill when the task concerns TurboDiffusion backend readiness or acceleration choices: CUDA extension builds, `turbo_diffusion_ops`, INT8 Linear, FastRMSNorm/FastLayerNorm, SLA/SageSLA, `attention_type`, `sla_topk`, `quant_linear`, `default_norm`, or source-layout import quirks.

## Route first

- For backend installation, extension build requirements, `CUDA_HOME`, `nvcc`, CUTLASS, and custom-op import checks, read [backend-build.md](references/backend-build.md).
- For API and option semantics around `SparseLinearAttention`, `SageSparseLinearAttention`, `Int8Linear`, FastNorm modules, and model replacement helpers, read [acceleration-api.md](references/acceleration-api.md).
- For symptom-to-fix matrices covering CUDA headers, `turbo_diffusion_ops`, `flash-attn`, missing SpargeAttn, `SAGESLA_ENABLED = false`, source-layout imports, and tiny SLA smoke warnings, read [troubleshooting.md](references/troubleshooting.md).
- To inspect a user's current environment without downloads or model execution, run [check_acceleration_backend.py](scripts/check_acceleration_backend.py).

## Boundaries

- User-facing T2V/I2V launch construction belongs to the sibling `video-inference` sub-skill.
- Interactive TUI serving belongs to the sibling `interactive-serving` sub-skill.
- Training launch, checkpoint conversion, and quantized checkpoint export command construction belong to the sibling `training-and-checkpoints` sub-skill.
- TurboT2AV's TileLang W8A8/FastNorm stack and Pixi/LTX-2 environment belong to the sibling `turbot2av-extension` sub-skill; only compare the concepts here.

## Operating procedure

1. Establish whether the user is checking an installed package, a source build, or runtime flag choices. Do not ask them to download checkpoints for backend-only checks.
2. Run the safe diagnostic script when backend state is unknown:

   ```bash
   python sub-skills/acceleration-backends/scripts/check_acceleration_backend.py
   ```

   Add `--require-cuda` only when the requested capability truly needs CUDA custom ops.
3. If `attention_type=sagesla` is requested, require SpargeAttn-backed `SageSparseLinearAttention`; otherwise route to the `sla` or `original` fallback decision in [acceleration-api.md](references/acceleration-api.md).
4. If a quantized checkpoint is used, require both `--quant_linear` and working `turbo_diffusion_ops`; if an unquantized checkpoint is used, do not add `--quant_linear` by habit.
5. If a command is run from a source checkout and imports fail for top-level modules such as `imaginaire`, `rcm`, `ops`, `SLA`, or `serve`, apply the source-layout `PYTHONPATH` note in [backend-build.md](references/backend-build.md) instead of hard-coding local paths.
