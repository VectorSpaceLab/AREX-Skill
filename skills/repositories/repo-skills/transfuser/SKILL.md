---
name: transfuser
description: "Guides TransFuser autonomous-driving model training, multimodal
  CARLA sensor-agent operation, dataset and route preparation, Longest6
  evaluation, and result analysis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# TransFuser

Use this repo skill when a task mentions TransFuser, transformer-based sensor
fusion for CARLA, camera/LiDAR imitation learning, `HybridAgent`, CARLA
Longest6, route/scenario generation, or the repository's training/evaluation
artifacts.

## Choose the route

- **Train, resume, validate data, select a fusion backbone, or inspect a
  checkpoint:** read [model-training](sub-skills/model-training/SKILL.md).
- **Configure or diagnose the learned CARLA sensor agent, sensors, target point,
  PID control, safety, or ensembles:** read
  [sensor-agent](sub-skills/sensor-agent/SKILL.md).
- **Validate dataset trees, route/scenario XML/JSON, generate routes, or plan
  privileged data collection:** read
  [data-and-routes](sub-skills/data-and-routes/SKILL.md).
- **Prepare local/Longest6 evaluation, parse result JSON, build a guarded
  evaluation/Docker plan, or interpret infractions:** read
  [carla-evaluation](sub-skills/carla-evaluation/SKILL.md).

Read [installation-and-compatibility.md](references/installation-and-compatibility.md)
first when setting up a new runtime, changing the legacy dependency stack, or
checking whether CUDA/CARLA prerequisites are available. Read
[troubleshooting.md](references/troubleshooting.md) when a workflow fails at
installation, import, data/config validation, backend setup, or external
runtime boundaries. Read [repo-provenance.md](references/repo-provenance.md)
before deciding whether this skill is stale for a changed checkout.

## Operating contract

1. Establish the checkout, dataset/checkpoint paths, requested backbone, target
   CARLA version, and whether the task is static preparation, a safe smoke, or
   full simulation/training.
2. Run the nearest bundled preflight before an expensive action. Bundled
   helpers are plan/validation tools: they do not download the 210-GB dataset,
   launch CARLA, train for epochs, build Docker images, or submit cloud jobs.
3. Preserve the repository's coordinate and file-layout conventions. Do not
   silently reinterpret camera/LiDAR axes, route IDs, DDP checkpoint prefixes,
   `args.txt`, or the `TEAM_CONFIG` directory contract.
4. Treat CUDA as required for learned training and inference. A CPU import or
   parser check is not a substitute. Treat CARLA 0.9.10.1 plus a running
   compatible server as required for simulation-native data generation and
   evaluation.
5. Keep external side effects explicit: ask for or verify network, disk,
   simulator, GPU, Docker, credentials, and checkpoint prerequisites before
   launching them.

## Installation and minimal checks

The historical repository environment is Python 3.7 with a CUDA 11.3 PyTorch
1.12.1 stack and matching OpenMMLab 1.x packages. Prefer the exact documented
combination for compatibility; do not upgrade one compiled component in
isolation. A minimal package-only check is:

```bash
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"
python scripts/check_environment.py --json
```

The learned workflows additionally need the repository's top-level modules on
`PYTHONPATH` or an equivalent checkout-aware launch context, compatible
`mmcv-full`, `mmdet`, `mmsegmentation`, `mmcls`, `torch-scatter`, `timm`, and
the data/vision dependencies. Full sensor-agent and CARLA evaluation also need
the CARLA 0.9.10.1 Python API, scenario-runner, leaderboard modules, a running
CARLA server, model checkpoints, and route/scenario files.

## Scope boundaries

This skill distills the public TransFuser operating workflows; it is not a
vendored copy of CARLA or ScenarioRunner. Large maps, figures, downloaded
weights, generated results, and the full dataset are not runtime dependencies
of this skill. Docker packaging and Alpha leaderboard submission are described
as guarded external workflows, not automatically executed.
