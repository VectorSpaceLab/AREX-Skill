---
name: deepspeed
description: "Use DeepSpeed for distributed training, inference acceleration,
  ZeRO configuration, parallelism/MoE design, profiling, autotuning, and
  operational diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DeepSpeed Repo Skill

Use this skill when a user asks to work with DeepSpeed APIs, configuration files, launch commands, inference acceleration, model parallelism, MoE, profiling, autotuning, or operational tooling. DeepSpeed is a PyTorch-focused optimization library with many optional GPU, distributed, and compiled-op paths, so route first by the user's workflow and then check the relevant troubleshooting reference before running heavy commands.

## First Checks

1. Confirm the user wants DeepSpeed itself, not a downstream framework integration that merely accepts a DeepSpeed config.
2. Read `references/install-and-environment.md` when installing, importing, or debugging optional CUDA/ROCm/vendor accelerator behavior.
3. Run `scripts/check_deepspeed_env.py` for a read-only environment check, then `scripts/inspect_deepspeed_api.py` when API fields or signatures may have drifted.
4. Check `references/repo-provenance.md` before refreshing this skill against a source checkout.
5. Do not run native examples, distributed tests, autotuning, NVMe/GDS tools, builds, downloads, or remote SSH commands without explicit safety confirmation.

## Route By Task

- Use `sub-skills/training-config/` for PyTorch training integration, `ds_config.json` authoring, launcher resource filters, ZeRO/offload choices, checkpoint save/load/export, and config validation.
- Use `sub-skills/inference-injection/` for `deepspeed.init_inference`, kernel or manual injection policies, inference tensor parallelism, inference quantization, checkpoint reshaping, v2/FastGen routing, and hybrid-engine boundaries.
- Use `sub-skills/parallelism-moe/` for `PipelineModule`, pipeline schedules, MoE layers and optimizer groups, expert tensor parallelism, sequence parallel APIs, AutoSP, and activation checkpointing.
- Use `sub-skills/ops-tooling/` for `ds_report`, install/build diagnostics, JIT/prebuilt op flags, autotuning, FLOPS profiling, monitor backends, DeepNVMe/AIO/GDS tools, compression APIs, and repo policy checks.

## Shared References

- `references/install-and-environment.md`: package installation, PyTorch-first requirement, optional extras, compiled ops, and backend safety tiers.
- `references/troubleshooting.md`: cross-cutting import, accelerator, config, launcher, and optional-tool failure modes.
- `references/repo-provenance.md`: source snapshot and refresh baseline.

## Shared Scripts

- `scripts/check_deepspeed_env.py`: read-only import, package metadata, PyTorch, CUDA visibility, and installed CLI discovery.
- `scripts/inspect_deepspeed_api.py`: read-only signature and config-field inspection for the main DeepSpeed APIs covered by this skill.

## Safety Defaults

- Prefer read-only commands first: imports, `--help`, config parsing, and tiny CPU checks.
- Treat `deepspeed` launcher commands, checkpoint tests, CUDA op builds, autotuning, `ds_io`, `ds_nvme_tune`, GDS/AIO code, and `ds_ssh` as real workload or infrastructure commands.
- Do not promise GPU, compiled-op, NVMe, GDS, monitor, or model-download behavior unless the current environment has been explicitly verified for that path.
- Keep generated examples self-contained. Do not tell future agents to open or execute original repo docs, tests, scripts, examples, or notebooks as runtime dependencies.
