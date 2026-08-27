---
name: simpledet
description: "Guides SimpleDet MXNet object detection and instance-recognition
  workflows, including legacy CUDA setup, roidb preparation, configurable
  training and evaluation, inference benchmarking, and detector customization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SimpleDet

Use this repo skill when a task names **SimpleDet**, `detection_train.py`,
`detection_test.py`, `mask_test.py`, `detection_infer_speed.py`, `mxnext`,
SimpleDet roidb files, or its symbolic detector/configuration APIs.

This is a legacy MXNet 1.x framework. Read the relevant route before proposing
commands; do not assume a modern MXNet/PyTorch environment is compatible.
Read [repo-provenance.md](references/repo-provenance.md) before deciding
whether this skill is stale.

## Route by task

- **Install, import, extension build, CUDA, checkpoints, logs, TensorBoard, or
  distributed prerequisites:** read [setup-and-operations/SKILL.md](sub-skills/setup-and-operations/SKILL.md).
- **COCO/VOC/CrowdHuman/JSON annotations, roidb generation, or validation:**
  read [data-preparation/SKILL.md](sub-skills/data-preparation/SKILL.md).
- **Train, evaluate, mask-test, benchmark speed, fine-tune, or select a config:**
  read [detection-workflows/SKILL.md](sub-skills/detection-workflows/SKILL.md).
- **Compose a detector, add a component, choose a model family, or change
  symbolic outputs:** read [model-customization/SKILL.md](sub-skills/model-customization/SKILL.md).

For a task spanning routes, start with setup-and-operations for runtime gates,
then data-preparation, then detection-workflows; use model-customization when
the architecture or config contract changes.

## Runtime contract

SimpleDet is checkout-driven rather than a normal installable package. The
public baseline is Python 3.7, NumPy 1.x, OpenCV, `pytz`, patched
`pycocotools`, `mxnext`, and a CUDA-enabled MXNet 1.6-era build. The standard
train/test/speed entry points construct `mx.gpu` contexts, so a CPU import is
not evidence that the main workflows run.

Before any long command:

1. Run [scripts/check_environment.py](scripts/check_environment.py) with
   `--repo-root` pointing at the checkout.
2. Inspect a config with
   [detection-workflows/scripts/inspect_config.py](sub-skills/detection-workflows/scripts/inspect_config.py).
3. Validate caches with
   [data-preparation/scripts/validate_roidb.py](sub-skills/data-preparation/scripts/validate_roidb.py).
4. Use [scripts/run_workflow.py](scripts/run_workflow.py) with `--dry-run` to
   inspect the exact entry point, config, and working directory.
5. Keep datasets, weights, logs, and experiments outside the generated skill.

The production inspection could not obtain the documented legacy CUDA wheel and
had no `nvcc`; CUDA execution is an explicit unresolved gate, not a verified
claim. Read [troubleshooting.md](references/troubleshooting.md) for the
consequence.

## Workflow wrapper

The wrapper makes checkout selection explicit and has no install/download/kill
behavior. Remove `--dry-run` only after backend, data, config, and checkpoint
checks pass:

```bash
python <skill-root>/scripts/run_workflow.py --repo-root /path/to/simpledet \
  --entrypoint speed --config config/faster_r50v1_fpn_1x.py \
  --shape 800 1333 --gpu 0 --count 100 --dry-run
```

The selected entry point may still allocate GPUs, read large data, load weights,
and write under `experiments/`.

## Shared references

- [references/troubleshooting.md](references/troubleshooting.md) covers
  cross-cutting import, data, config, checkpoint, and backend failures.
- [references/coverage-notes.md](references/coverage-notes.md) records the
  integrated scope and intentional omissions.
