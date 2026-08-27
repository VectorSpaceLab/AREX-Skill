---
name: spikingjelly
description: "Operate the SpikingJelly package for SNN modeling, datasets,
  ANN-to-SNN conversion, backend performance, training scale-out, and deployment
  exchange."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# SpikingJelly Repo Skill

Use this skill when the task is about the public `spikingjelly` package rather than a one-off source edit.

## Start here

1. Install PyTorch first, then install `spikingjelly` plus only the extras needed for the selected workflow.
2. Run [`scripts/spikingjelly_env_report.py`](scripts/spikingjelly_env_report.py) to confirm the installed package, torch, and optional backends; consult [`references/repo-provenance.md`](references/repo-provenance.md) for the source anchor.
3. Choose the smallest matching sub-skill below.
4. Use the sub-skill's bundled references and smoke script before larger runs.

## Route map

- `sub-skills/core-snn/` — activation-based SNN modeling, step modes, reset/state, surrogate gradients, neurons, layers, recurrent wrappers, monitors, timing-based helpers, visualizing, configure, and logger.
- `sub-skills/datasets/` — neuromorphic dataset loading, builders, transforms, utilities, and manual-download workflows.
- `sub-skills/ann2snn/` — ANN-to-SNN conversion, calibration, transformer/Qwen2 recipes, and readout semantics.
- `sub-skills/performance-and-analysis/` — CUDA/CuPy/Triton, FlexSN, precision, memory optimization, op counting, and energy/profiling.
- `sub-skills/training-and-scaleout/` — model zoo, training helpers, distributed vision, and scale-out topologies.
- `sub-skills/deployment-exchange/` — NIR, Lava, and Lynxi exchange and deployment.

## Shared references

- `references/package-overview.md`
- `references/repo-provenance.md`
- `references/troubleshooting.md`

## Shared script

- `scripts/spikingjelly_env_report.py`: lightweight environment and import report.

## Safe defaults

- Prefer public package imports over source-checkout paths in runtime instructions.
- Treat optional accelerators and vendor stacks as optional unless a sub-skill explicitly verified them in the current environment.
- Keep each task in the narrowest branch that answers the user request.
