---
name: package-apis
description: "Inspect and use detrex Python APIs for layers, losses, matchers,
  backbones, data mappers, config helpers, checkpointing, EMA, distributed
  utilities, and WandB writer."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# detrex package APIs

Use this sub-skill when the task is to import, inspect, instantiate, or debug detrex Python APIs rather than run a training, evaluation, demo, or model-zoo workflow.

## Fast route

1. If the user is unsure whether detrex is importable, run the bundled helper first:
   - `python scripts/api_smoke.py --help` to see safe checks.
   - `python scripts/api_smoke.py --strict` to inspect public imports and signatures without downloads or training.
   - Add `--check-cuda-extension` only when the user specifically needs the compiled multi-scale deformable-attention extension.
2. Read [references/api-reference.md](references/api-reference.md) for layers, losses, matchers, config helpers, checkpointing, EMA, distributed helpers, and WandB writer usage.
3. Read [references/backbones-and-data.md](references/backbones-and-data.md) when the task involves `ResNet`, `TimmBackbone`, `TorchvisionBackbone`, `ChannelMapper`, data mappers, transforms, or feature-shape wiring.
4. Read [references/troubleshooting.md](references/troubleshooting.md) when imports fail, CUDA operators are missing, LazyConfig lookup fails, a matcher or loss signature is confusing, a mapper cannot consume a dataset dict, or WandB/distributed/checkpoint behavior is surprising.

## Operating rules

- Prefer public package imports such as `detrex.layers`, `detrex.modeling`, `detrex.modeling.backbone`, `detrex.data`, `detrex.config`, `detrex.checkpoint`, and `detrex.utils`.
- Do not rely on the repository source tree being present. Use installed-package imports or user-provided code/config paths.
- Do not trigger downloads by default. For backbone experiments, set `pretrained=False` unless the user explicitly asks for pretrained weights and has arranged caches/network access.
- Do not run training, evaluation, dataset registration, native repo tests, or large CUDA kernels just to answer an API question. Use the bundled smoke helper for inspection and escalate only if the user asks for backend verification.
- Treat compiled operators (`detrex._C`, multi-scale deformable attention, DCNv3) as backend-sensitive. Inspect availability before constructing workflows that require them.
