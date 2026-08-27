---
name: pytracking
description: "Use PyTracking and LTR for visual object tracking, video object
  segmentation, tracker evaluation, result analysis, custom tracker development,
  and PyTorch training workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# PyTracking Repo Skill

Use this skill when a task involves PyTracking, LTR, or visual object tracking/video object segmentation workflows from the PyTracking repository: running pretrained trackers, configuring datasets and checkpoints, analyzing benchmark results, packaging submissions, implementing custom trackers, or training LTR models.

## First checks

1. Read [repository provenance](references/repo-provenance.md) when deciding whether this skill matches a target checkout or whether `refresh-repo-skill` is needed.
2. Read [configuration and environment](references/configuration.md) before running anything that needs datasets, checkpoints, CUDA, Visdom, VOT, or training workspaces.
3. Use the read-only setup checker before execution:

   ```bash
   python scripts/check_pytracking_setup.py --repo-root /path/to/pytracking --require-dataset otb
   ```

4. For tracker/model name selection, read [tracker and model catalog](references/tracker-and-model-catalog.md).
5. For install/import/backend/data/checkpoint failures that do not belong to one workflow, read [cross-cutting troubleshooting](references/troubleshooting.md).

## Route by task

| Task shape | Read next |
| --- | --- |
| Run a tracker on a dataset, one sequence, a video, webcam, or an experiment function; choose dataset aliases; reason about `run_tracker`, `run_video`, `run_webcam`, `run_experiment`, `Tracker`, `trackerlist`, debug, Visdom, and result directories. | [tracking-evaluation](sub-skills/tracking-evaluation/SKILL.md) |
| Analyze saved bounding-box/VOS results, plan plots, replay outputs, package GOT-10k or TrackingNet submissions, handle raw result archives, or plan VOT toolkit integration. | [analysis-and-packaging](sub-skills/analysis-and-packaging/SKILL.md) |
| Configure, launch, inspect, or modify LTR training settings, datasets, samplers, actors, trainers, models, checkpoints, TensorBoard, and CUDA training behavior. | [ltr-training](sub-skills/ltr-training/SKILL.md) |
| Implement, adapt, register, or debug a custom tracker or parameter file; inspect `BaseTracker`, `TrackerParams`, output dictionaries, multi-object/segmentation conventions, features, and tracking libs. | [tracker-development](sub-skills/tracker-development/SKILL.md) |

## Operating boundaries

- This skill teaches PyTracking operation; it does not contain pretrained model weights, datasets, raw benchmark results, or VOT workspaces.
- Full tracker and training workflows usually need a CUDA-capable PyTorch environment plus external datasets/checkpoints. CPU import checks are useful for command/config validation but are not proof of full tracker performance.
- The upstream shell installer is broad and side-effecting. Do not run it automatically; translate the selected workflow into minimal environment, dependency, data, and checkpoint checks.
- Do not launch full benchmark evaluations, training epochs, webcam/video GUI sessions, Visdom servers, VOT toolkits, Google Drive downloads, or archive packaging without explicit user approval for side effects, runtime, data, and hardware.
- PyTracking is source-tree-style in this snapshot. Commands commonly run from a target checkout root or with that checkout root on `PYTHONPATH`; avoid assuming a normal `pip install .` package.

## Minimal import and CUDA smoke

Use this in the user's target environment before claiming runtime readiness:

```bash
python - <<'PY'
import torch
import pytracking, ltr
print('pytracking', pytracking.__file__)
print('ltr', ltr.__file__)
print('torch', torch.__version__, 'cuda_available', torch.cuda.is_available())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
    torch.empty((1,), device='cuda')
PY
```

If CUDA is unavailable, narrow the task to source/config/command planning or use only explicitly CPU-capable mechanics; do not report network-backed tracker/training execution as verified.

## Common commands to plan, not blindly run

Build a dataset command without executing it:

```bash
python sub-skills/tracking-evaluation/scripts/build_tracking_command.py dataset --tracker dimp --param dimp50 --dataset otb --sequence Soccer --debug 0 --explain
```

Build an LTR training command without launching training:

```bash
python sub-skills/ltr-training/scripts/build_training_command.py --repo-root /path/to/pytracking bbreg atom --explain
```

Plan a benchmark packaging layout without writing a zip:

```bash
python sub-skills/analysis-and-packaging/scripts/plan_result_packaging.py got10k --tracker-name dimp --parameter-name dimp50 --run-ids 0,1,2
```

Validate a custom tracker layout statically:

```bash
python sub-skills/tracker-development/scripts/validate_tracker_layout.py --repo-root /path/to/pytracking --tracker-name mytracker --param-name default
```

## Verification stance

Generated guidance is self-contained in this skill tree. Source repository files were used as evidence, but runtime Markdown links and bundled scripts point inside this skill. When a future task needs real PyTracking execution, validate the target checkout, environment, datasets, checkpoints, and side effects first, then route to the focused sub-skill.
