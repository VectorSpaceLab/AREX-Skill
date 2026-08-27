# Evaluation and Checkpointing

## Evaluator Selection

Detectron2 evaluation is built around `DatasetEvaluator`:

- `reset()`: prepare for a new evaluation round.
- `process(inputs, outputs)`: consume model inputs and outputs.
- `evaluate()`: return a dict of metrics, often nested by task such as `{"bbox": {"AP50": 80.0}}`.

Use built-in evaluators when the dataset and task match:

- `COCOEvaluator(dataset_name, tasks=None, distributed=True, output_dir=None, *, max_dets_per_image=None, use_fast_impl=True, kpt_oks_sigmas=(), allow_cached_coco=True)` for detection, instance segmentation, and keypoints on COCO-format or standard-format datasets.
- `SemSegEvaluator` for semantic segmentation standard-format datasets.
- `DatasetEvaluators([evaluator_a, evaluator_b])` to combine multiple evaluators in one pass.
- Dataset-specific evaluators such as LVIS, Pascal VOC, Cityscapes, and panoptic evaluators when metadata and task type match.

`COCOEvaluator` requires either dataset metadata with `json_file` or an `output_dir` so it can convert standard-format records to COCO JSON. If predictions contain class ids outside the dataset's contiguous id range, evaluation raises an assertion; check class count and metadata mapping.

## Manual Evaluation Pattern

Use this API shape in custom scripts after dataset registration and config/model construction:

```python
from detectron2.checkpoint import DetectionCheckpointer
from detectron2.data import build_detection_test_loader
from detectron2.evaluation import COCOEvaluator, inference_on_dataset
from detectron2.modeling import build_model

model = build_model(cfg)
DetectionCheckpointer(model).load(cfg.MODEL.WEIGHTS)
model.eval()
loader = build_detection_test_loader(cfg, dataset_name)
evaluator = COCOEvaluator(dataset_name, output_dir=cfg.OUTPUT_DIR)
results = inference_on_dataset(model, loader, evaluator)
```

`inference_on_dataset(model, data_loader, evaluator, callbacks=None)` temporarily puts `nn.Module` models in eval mode, wraps inference in `torch.no_grad()`, logs data/compute/eval timing, calls `evaluator.process`, and returns `evaluator.evaluate()` or `{}` if the evaluator returns `None` on non-main workers.

Do not use `inference_on_dataset` for hidden long benchmarks without user approval; it runs a full pass over the loader.

## `DefaultTrainer.test` and `verify_results`

`DefaultTrainer.test(cfg, model, evaluators=None)` iterates over `cfg.DATASETS.TEST`, builds a test loader per dataset, and either uses supplied evaluators or calls `build_evaluator`. If no evaluator is available, it logs a warning and returns `{}` for that dataset.

Use `verify_results(cfg, results)` only when `cfg.TEST.EXPECTED_RESULTS` is populated and the expected metrics are meaningful for the current dataset/checkpoint. It is normally called on the main process after eval-only or final training evaluation.

## Checkpointer Behavior

`DetectionCheckpointer(model, save_dir='', *, save_to_disk=None, **checkpointables)` extends fvcore `Checkpointer` for Detectron2 model-zoo and legacy checkpoints. It can:

- Load Detectron2 `.pth` files with `{"model": state_dict}` or raw PyTorch state dicts.
- Load legacy `.pkl` Detectron/Caffe2 checkpoints and `.pyth` pycls checkpoints with conversion heuristics.
- Accept `?matching_heuristics=True` on a checkpoint path to align legacy state dict names by heuristics.
- Coordinate distributed loading when not all workers can read the checkpoint.
- Save checkpointable trainer/optimizer/scheduler state when those objects are passed as keyword arguments.

Important methods:

- `load(path)`: load the specified path now; usually model weights only unless checkpointables are present and state exists.
- `resume_or_load(path, resume=True)`: if `resume=True` and `save_dir/last_checkpoint` exists, resume from that checkpoint; otherwise load `path`.
- `has_checkpoint()`: true when `last_checkpoint` exists in the save directory.
- `save(name, **kwargs)`: save model plus checkpointables under `save_dir` on the main process.

For `DefaultTrainer.resume_or_load(resume=True)`, a true resume restores trainer state and sets `start_iter` to the next iteration after the checkpoint's stored iteration. A fresh load starts at iteration 0.

## Checkpoint Path Choices

- Fresh fine-tune from model-zoo or pretrained weights: set `MODEL.WEIGHTS` for Yacs or `train.init_checkpoint` for LazyConfig, choose a new `OUTPUT_DIR`, and do not pass `--resume`.
- Continue an interrupted Yacs run: keep the same `OUTPUT_DIR` and pass `--resume`.
- Evaluate a final model: pass `--eval-only` and set `MODEL.WEIGHTS`/`train.init_checkpoint` to the desired checkpoint.
- Evaluate the most recent interrupted run: pass both `--eval-only` and `--resume` only when `OUTPUT_DIR/last_checkpoint` points to the intended checkpoint.

## Evaluation Plan Checklist

Before evaluation, verify:

1. The dataset is registered in `DatasetCatalog` and has usable metadata.
2. The evaluator matches the dataset type and expected outputs.
3. The checkpoint path exists or is a resolvable model-zoo URL/path.
4. Class count and metadata mappings match the trained model.
5. `OUTPUT_DIR` is writable for evaluator output files.
6. Multi-GPU/multi-machine settings are intentional and approved.

The bundled helper `scripts/evaluation_plan.py` prints this checklist and suggested command/API shape without running evaluation.
