---
name: diffusion-planner
description: "Use Diffusion Planner for nuPlan autonomous-driving trajectory
  generation: prepare model-ready data, train or resume the diffusion model,
  configure closed-loop planning, and add differentiable collision or classifier
  guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Diffusion Planner

Use this repo skill when a Researcher needs to operate the Diffusion Planner
implementation for nuPlan autonomous-driving motion planning. It is a router,
not a replacement for the nuPlan devkit or the external dataset/checkpoint
artifacts.

## Start here

1. Identify the requested stage: data preparation, model training/resume,
   ordinary closed-loop planning, or custom/guided sampling.
2. Confirm the environment and external inputs before starting an expensive
   operation. Full training, simulation, and guidance require a CUDA-capable
   PyTorch environment; real workflows also require nuPlan data/maps and, for
   inference, a matching `args.json` plus checkpoint.
3. Run the owning sub-skill's bounded preflight before launching workers,
   downloading artifacts, or writing a long-running run directory.
4. Preserve the exact model configuration, normalization file, manifest, split,
   checkpoint, device mapping, and first failure signal in the handoff.

## Routes

- [data-preparation](sub-skills/data-preparation/SKILL.md) — convert nuPlan
  scenarios into fixed-size `.npz` records and a JSON filename manifest;
  validate feature axes, paths, and normalization.
- [model-training](sub-skills/model-training/SKILL.md) — validate the model/data
  contract, run bounded PyTorch checks, launch CUDA/DDP training, and resume
  checkpoints with EMA and optimizer-state caveats.
- [closed-loop-planning](sub-skills/closed-loop-planning/SKILL.md) — configure
  `DiffusionPlanner`, trajectory sampling, checkpoint loading, scenario
  filters/builders, Ray simulation, and optional NuBoard inspection.
- [guidance](sub-skills/guidance/SKILL.md) — implement or debug differentiable
  custom guidance, collision energy, normalization/device handling, and guided
  simulation.

The usual dependency order is `data-preparation` → `model-training` →
`closed-loop-planning`; `guidance` branches from a compatible planner/checkpoint
and then returns to `closed-loop-planning` for execution.

## Installation and environment gate

The source package metadata identifies distribution `diffusion_planner` at
version `1.0.0` and targets Python 3.9. Install the repository package in the
active environment, then install the CUDA-aware requirements selected for the
workflow. The documented baseline pins PyTorch `2.0.0+cu118` and torchvision
`0.15.1+cu118`; use a compatible wheel rather than silently substituting a CPU
build for a CUDA workflow. Install a matching nuPlan-devkit separately for
scenario/map/simulation APIs.

For a checkout of the package, install the public distribution and the
workflow-selected requirements in the active environment:

```bash
python -m pip install -e .
python -m pip install -r requirements_torch.txt
```

Install a compatible nuPlan-devkit separately for scenario, map, and
simulation APIs. A minimal package import check is:

```bash
python -c "import torch, diffusion_planner; print(torch.__version__, torch.cuda.is_available())"
```

For full preflight, also import the owning modules and run the bundled checks
linked by that sub-skill. Do not mutate a shared/base environment merely to
repair optional dependencies. Keep external dataset, map, checkpoint,
experiment-root, and credentials out of generated skill files and command
transcripts intended for publication.

## Shared operating rules

- Treat `args.json` and a checkpoint as a pair. `args.json` supplies model
  dimensions and serialized normalizers; a `.pth` filename alone is not proof
  of compatibility.
- Keep the model-ready manifest as relative `.npz` filenames under one data
  directory. Validate a small sample before DDP or scenario workers start.
- Do not copy the repository's `sudo`, placeholder, private-interpreter, or
  eight-GPU shell invocations verbatim. Adapt them to the active environment,
  visible devices, and approved output paths.
- A parser/import or synthetic tensor check is not a real training or
  closed-loop result. Report missing data, maps, checkpoints, Ray, or hardware
  as explicit gates.
- Prefer a tiny, deterministic helper or preflight over an expensive native
  command. Stop on the first contract failure and route it to the owning
  sub-skill.
- The implementation has source-backed quirks: the default device is CUDA,
  DDP floor-divides global batch size without checking divisibility, disabling
  EMA is not currently flag-only safe, and the scheduler name overstates its
  post-warmup behavior. Read the model-training references before adapting
  these paths.

## Shared references

- Read [repository provenance](references/repo-provenance.md) before deciding
  whether this skill matches a checkout or needs refresh.
- Read [cross-cutting troubleshooting](references/troubleshooting.md) for
  installation/import, optional dependency, path/config, backend, checkpoint,
  and external-artifact failures.
- Run [the environment probe](scripts/check_environment.py) for a safe import,
  version, and CUDA diagnostic; it never downloads data or starts simulation.
- Use the generated sub-skill references for API tables, schemas, command
  details, and difficult-case recovery. Review artifacts and verification
  reports belong outside this runtime tree.

## Stop conditions

Stop and report instead of claiming success when the selected required backend
cannot initialize, the package imports only through an unintended checkout,
the manifest or normalization contract is invalid, checkpoint/config keys do
not match, or external nuPlan data/maps/checkpoints are absent for a requested
native run. This graph was generated from commit `a3a621f`; see provenance for
the complete baseline and refresh signals.
