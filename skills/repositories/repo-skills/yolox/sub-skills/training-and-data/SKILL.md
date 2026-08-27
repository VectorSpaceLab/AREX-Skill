---
name: training-and-data
description: "Design and validate YOLOX training, data, Exp, caching, logging,
  and evaluation experiments."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# YOLOX Training And Data

Use this sub-skill when a task involves YOLOX training or evaluation setup, dataset layout, custom `Exp` files, config overrides, caching, image-size behavior, freezing, assignment visualization, or training loggers. Full training and evaluation are dataset-, checkpoint-, and accelerator-dependent; this sub-skill helps plan and validate them before expensive runs.

Route PyTorch demo inference and `postprocess`/`vis` details to `../inference-and-api/SKILL.md`. Route ONNX, TorchScript, TensorRT, or deployment exports to `../export-and-deployment/SKILL.md`.

## Read or run these first

- Read [references/training-workflows.md](references/training-workflows.md) for train/eval commands, distributed flags, image-size controls, freezing, assignment visualization, and TensorBoard/MLflow/W&B logging.
- Read [references/data-and-exp-reference.md](references/data-and-exp-reference.md) when preparing COCO/VOC/custom datasets, writing an `Exp`, using `YOLOX_DATADIR`, applying `opts`, or reasoning about caching/default model sizes.
- Read [references/troubleshooting.md](references/troubleshooting.md) for annotation, image, class-count, checkpoint, cache, distributed, logger, resume, or evaluator failures.
- Run [scripts/inspect_yolox_exp.py](scripts/inspect_yolox_exp.py) before expensive training to load an `Exp`, inspect fields, and optionally check COCO/VOC paths without starting dataloaders or training.

## Fast operating rules

1. Prefer installed module commands such as `python -m yolox.tools.train`, `python -m yolox.tools.eval`, and `python -m yolox.tools.visualize_assign`.
2. Specify exactly one experiment source: `-n yolox-s` for a packaged default or `-f path/to/exp.py` for custom data/classes/architecture. If both are supplied to `get_exp`, the file wins.
3. Keep dataset roots explicit. Set `YOLOX_DATADIR` for built-in COCO/VOC-style experiments, or set `self.data_dir` in the `Exp` for custom COCO layouts.
4. Validate `num_classes`, `input_size`, `test_size`, annotations, image directories, and checkpoint compatibility before multi-GPU or cached runs.
5. Treat `--cache` as a resource decision: RAM cache is fast but memory-heavy; disk cache needs writable dataset-root storage.
6. Put non-default architecture, dataset, evaluator, augmentation, image-size, freezing, optimizer, or scheduler behavior in an `Exp` subclass. Use CLI `opts` only for small typed overrides of existing fields.

## Safe Exp inspection

From this sub-skill directory:

```bash
python scripts/inspect_yolox_exp.py --name yolox-s --expected-format none
python scripts/inspect_yolox_exp.py --exp-file path/to/exp.py --check-data --expected-format coco
```

The helper never starts training/evaluation. Missing dataset paths under `--check-data` are reported as preflight failures so the user can fix paths before launching YOLOX.
