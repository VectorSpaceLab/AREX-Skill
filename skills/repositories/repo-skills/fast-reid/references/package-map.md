# FastReID package map

Read this when you need a compact map of FastReID's public modules and verified
runtime facts before choosing a sub-skill.

## Package identity

- Import root: `fastreid`.
- Version in this checkout: `1.3`.
- Packaging status: source-only checkout; there is no `setup.py` or
  `pyproject.toml` in the inspected commit. Make a local checkout importable
  through `PYTHONPATH`, a `.pth` file, or a wrapper's explicit `--repo-root`.
- Default device: `MODEL.DEVICE` is `cuda`; CPU smoke checks must override it.
- Python compatibility: this older codebase is safest on Python 3.9. Python
  3.10+ can expose compatibility failures in code paths that import deprecated
  `collections` aliases.

## Major modules

| Area | Public modules | Use |
|---|---|---|
| Config | `fastreid.config`, `fastreid.config.CfgNode`, `get_cfg`, `configurable` | Create/merge/freeze configs, `_BASE_` YAML inheritance, CLI `opts`. |
| Data | `fastreid.data`, `fastreid.data.datasets`, `DATASET_REGISTRY`, `ImageDataset`, `CommDataset` | Built-in datasets, custom dataset registration, transforms, samplers, dataloaders. |
| Modeling | `fastreid.modeling`, `build_model`, `build_backbone`, `build_heads` | Meta-architectures, backbones, heads, losses, feature tensors. |
| Engine | `fastreid.engine`, `DefaultTrainer`, `DefaultPredictor`, `launch`, `default_argument_parser` | Standard train/eval launcher, predictor, distributed launch, setup/logging. |
| Solver | `fastreid.solver`, `build_optimizer`, `build_lr_scheduler` | Optimizers, LR schedulers, gradient clipping, contiguous parameters. |
| Evaluation | `fastreid.evaluation`, `ReidEvaluator`, `inference_on_dataset`, `fastreid.evaluation.rank.evaluate_rank` | ReID metrics, CMC/mAP/mINP, Python/Cython rank fallback, AQE/rerank. |
| Utilities | `fastreid.utils.checkpoint.Checkpointer`, `events`, `logger`, `visualizer`, `compute_dist` | Checkpointing, logging/writers, visualization, distances. |
| Extension projects | project packages such as `fastattr`, `fastclas`, `fastdistill`, `fastface`, `fastretri`, `partialreid`, `naic` | Additional registry entries, config hooks, training variants, deployment/FastRT patterns. |

## Verified signatures

- `get_cfg() -> CfgNode`
- `CfgNode.merge_from_file(self, cfg_filename: str, allow_unsafe: bool = False)`
- `CfgNode.merge_from_list(self, cfg_list: list)`
- `default_argument_parser()`
- `launch(main_func, num_gpus_per_machine, num_machines=1, machine_rank=0, dist_url=None, args=())`
- `DefaultTrainer(cfg)` and `DefaultTrainer.test(cfg, model)`
- `DefaultPredictor(cfg)`
- `build_reid_train_loader(train_set, *, sampler=None, total_batch_size, num_workers=0)`
- `build_reid_test_loader(test_set, test_batch_size, num_query, num_workers=4)`
- `build_model(cfg)`, `build_backbone(cfg)`, `build_heads(cfg)`
- `build_optimizer(cfg, model, contiguous=True)`
- `build_lr_scheduler(cfg, optimizer, iters_per_epoch)`
- `ReidEvaluator(cfg, num_query, output_dir=None)`
- `inference_on_dataset(model, data_loader, evaluator, flip_test=False)`
- `evaluate_rank(distmat, q_pids, g_pids, q_camids, g_camids, max_rank=50, use_metric_cuhk03=False, use_cython=True)` from `fastreid.evaluation.rank`

## Registry highlights

- Dataset registry includes person ReID datasets such as `Market1501`,
  `DukeMTMC`, `MSMT17`, `CUHK03`, `VIPeR`, `GRID`, `iLIDS`, `PRAI`, `PKU`,
  `SYSU_mm`, and vehicle ReID datasets such as `VeRi`, `VehicleID`,
  `SmallVehicleID`, `MediumVehicleID`, `LargeVehicleID`, `VeRiWild`,
  `SmallVeRiWild`, `MediumVeRiWild`, and `LargeVeRiWild`.
- Backbone registry includes builders for ResNet, ResNeXt, ResNeSt, RepVGG,
  OSNet, MobileNetV2/V3, ShuffleNetV2, EfficientNet/RegNet, and ViT.
- Meta-architecture registry includes `Baseline`, `MGN`, `MoCo`, and
  `Distiller` in the core package; projects can add more.
- Head registry includes `EmbeddingHead` and `ClasHead` in core; projects add
  task-specific heads such as attribute, face, and partial-ReID heads.

## Optional dependency map

| Dependency/backend | Required for | Notes |
|---|---|---|
| PyTorch + torchvision | Core models, training/eval, transforms, predictor. | CPU works for import/config/model smoke; realistic training is CUDA-oriented. |
| `yacs`, `pyyaml` | Config nodes and YAML merge. | Missing `yacs` usually blocks `fastreid.config`. |
| OpenCV (`cv2`) | Demo image I/O, preprocessing, visualization. | Use headless OpenCV in server environments. |
| `faiss` / `faiss-cpu` | Optional retrieval/ranking acceleration. | CPU fallback can work; GPU FAISS is not required for base inspection. |
| Cython compiler | Optional rank evaluation acceleration. | Without compiled extension, FastReID warns and uses Python evaluation. |
| ONNX stack (`onnx`, `onnxoptimizer`, `onnxsim`, `onnxruntime`) | ONNX export and inference. | Export and runtime dependencies are separate. |
| Caffe/PyCaffe | Caffe export/inference. | Optional and often environment-specific. |
| TensorRT + CUDA | TensorRT/FastRT export/inference. | Optional NVIDIA runtime; no CPU substitute for engine validation. |

## Route from this map

- For source-only setup, config merge, and model-zoo recipes, use
  `sub-skills/setup-and-configuration/`.
- For dataset roots, layouts, registration, and loader behavior, use
  `sub-skills/data-and-datasets/`.
- For model construction, feature extraction, and predictor behavior, use
  `sub-skills/modeling-and-inference/`.
- For train/eval command construction, trainers, solvers, metrics, and logs,
  use `sub-skills/training-and-evaluation/`.
- For ONNX/Caffe/TensorRT export or extension projects, use
  `sub-skills/deployment-and-projects/`.
