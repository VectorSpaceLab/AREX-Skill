---
name: flash-linear-attention
description: "Operate Flash Linear Attention package workflows: setup, kernels,
  layers/models, KDA/context parallel, and benchmarking."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Flash Linear Attention Repo Skill

Use this repo skill for tasks involving Flash Linear Attention (FLA), the `fla` Python package, its Triton-based linear-attention operators, fused modules, Transformers-compatible model families, Kimi Delta Attention (KDA), context-parallel routes, and FLA-specific benchmark or maintainer workflows.

Read `references/repo-provenance.md` before deciding whether this skill is current for a checkout. If the commit, package version, public API, or evidence paths differ materially, refresh this skill before relying on detailed guidance.

## Fast routing

| User task | Read |
| --- | --- |
| Install/import FLA, choose CUDA/ROCm/XPU/NPU/CPU extras, inspect runtime versions, debug backend wheel or env-var issues. | `sub-skills/setup-and-backends/SKILL.md` |
| Call or maintain `fla.ops` functions, debug `@dispatch` fallback, select op tests, or reason about Triton kernel correctness. | `sub-skills/ops-kernels-and-dispatch/SKILL.md` |
| Use `fla.layers`, `fla.modules`, `fla.models`, Hugging Face `AutoModelForCausalLM`, generation, training, evaluation, or fused losses. | `sub-skills/layers-and-models/SKILL.md` |
| Work on KDA, `KimiDeltaAttention`, `KDAConfig`, `chunk_kda`, safe gates, FlashKDA/TileLang KDA, or context parallel. | `sub-skills/kda-and-context-parallel/SKILL.md` |
| Build correctness-gated benchmark commands, interpret speedups, run optimization loops, or summarize benchmark JSON. | `sub-skills/benchmarking-and-optimization/SKILL.md` |

## Minimal package setup facts

- Import package: `fla`.
- Main distribution: `flash-linear-attention` for layers/models plus core kernels.
- Core distribution: `fla-core` for `fla.ops`, `fla.modules`, and `fla.utils`-only users.
- Python: `>=3.10`.
- Base dependencies: `transformers>=4.45.0` and `einops`.
- `torch` and the correct Triton flavor are intentionally selected through backend extras, not the bare package install.

Typical install choices:

```bash
# NVIDIA CUDA
pip install 'flash-linear-attention[cuda]'

# ROCm: install torch from the PyTorch ROCm index first, then FLA.
pip install --index-url https://download.pytorch.org/whl/rocm7.2 torch
pip install 'flash-linear-attention[rocm]'

# CPU import-only or limited CPU checks.
pip install --index-url https://download.pytorch.org/whl/cpu torch
pip install 'flash-linear-attention[cpu]'
```

For XPU, NPU/Ascend, source installs, and `--no-deps` workflows, route to `sub-skills/setup-and-backends/SKILL.md`.

## Safe first checks

From the owning sub-skill directories, these bundled scripts avoid downloads, training, native tests, and destructive writes:

```bash
# Setup/import/backend visibility.
python sub-skills/setup-and-backends/scripts/check_fla_runtime.py --show-env-vars

# Public operator names/signatures without running kernels.
python sub-skills/ops-kernels-and-dispatch/scripts/inspect_fla_ops.py --filter gla

# Tiny layer/model construction without checkpoint downloads.
python sub-skills/layers-and-models/scripts/smoke_layer_model.py --device cpu

# KDA import and optional tiny CUDA KDA smoke.
python sub-skills/kda-and-context-parallel/scripts/smoke_kda.py --help

# Build a gated benchmark command without running it.
python sub-skills/benchmarking-and-optimization/scripts/fla_verify_op_command.py --op chunk_gla --base main
```

Use CUDA-requiring script flags only when the active environment intentionally has CUDA hardware and matching wheels.

## Cross-cutting operating rules

- Do not treat CPU import success as proof that Triton/CUDA, ROCm, XPU, NPU, TileLang, FlashKDA, or context-parallel kernels work.
- Set `FLA_*` backend and cache environment variables before starting Python; dispatch decisions are made in the active process.
- For maintainer tasks in an FLA checkout, correctness gates come before performance claims. A red or skipped gate means no speedup can be promoted.
- Do not change public layer/model symbols, config fields, checkpoint compatibility, validated numerical precision, or tolerances without explicit approval.
- Keep KDA-specific gate and CP behavior out of generic ops guidance; KDA has its own per-key-dimension gate and context-parallel constraints.

## References

- `references/package-overview.md` — package surfaces, supported workflow map, public exports, and optional dependency boundaries.
- `references/troubleshooting.md` — cross-cutting install/import/runtime triage before selecting a deeper sub-skill.
- `references/repo-provenance.md` — source commit, package version, evidence paths, and refresh checklist.
- `references/repo-routing-metadata.json` — structured router metadata for managed import tooling.
