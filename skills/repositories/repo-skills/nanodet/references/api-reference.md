# API reference

This reference summarizes the verified public builders and helper APIs that matter most for NanoDet users.

## Package basics

- Package name: `nanodet`
- Version: `1.0.0`
- Main import root: `nanodet`
- The package is installed from `setup.py` and exposes the source package tree under `nanodet/`.

## Verified builder and utility signatures

| Object | Signature | Purpose | Notes |
| --- | --- | --- | --- |
| `nanodet.model.arch.build_model` | `(model_cfg)` | Build the detector model from a config node | Accepts `GFL` as a deprecated alias for `OneStageDetector`; supports `OneStageDetector` and `NanoDetPlus` |
| `nanodet.model.backbone.build_backbone` | `(cfg)` | Build a backbone module | Supports `ResNet`, `ShuffleNetV2`, `GhostNet`, `MobileNetV2`, `EfficientNetLite`, `CustomCspNet`, `RepVGG`, and `TIMMWrapper` |
| `nanodet.model.fpn.build_fpn` | `(cfg)` | Build the neck / FPN module | Supports `FPN`, `PAN`, `TAN`, and `GhostPAN` |
| `nanodet.model.head.build_head` | `(cfg)` | Build the head module | Supports `GFLHead`, `NanoDetHead`, `NanoDetPlusHead`, and `SimpleConvHead` |
| `nanodet.data.dataset.build_dataset` | `(cfg, mode)` | Build a dataset instance for `train`, `val`, or `test` | Supports `CocoDataset`, `XMLDataset`, and `YoloDataset` |
| `nanodet.evaluator.build_evaluator` | `(cfg, dataset)` | Build an evaluator | Verified `CocoDetectionEvaluator` |
| `nanodet.optim.build_optimizer` | `(model, config)` | Build a torch optimizer with param-wise overrides | Supports standard `torch.optim` names plus `lr_mult`, `decay_mult`, `no_norm_decay`, and `no_bias_decay` |
| `nanodet.util.load_config` | `(cfg, args_cfg)` | Merge a YAML config file into a `CfgNode` | The loaded config is frozen after merge |
| `nanodet.util.load_model_weight` | `(model, checkpoint, logger)` | Load checkpoint weights into a model | Handles `module.` / `model.` prefixes and logs shape mismatches |
| `nanodet.util.convert_old_model` | `(old_model_dict)` | Convert legacy `.pth` checkpoints to Lightning-style `.ckpt` format | Used by the training and test scripts |
| `nanodet.util.convert_avg_params` | `(checkpoint)` | Extract averaged parameters from a checkpoint | Used by EMA-aware loading |
| `nanodet.util.mkdir` | `(local_rank=-1, *args, **kwargs)` | Rank-aware directory creation helper | Wrapped with `rank_filter` |
| `nanodet.util.collect_files` | `(path, exts)` | Recursively collect files by extension | Used by config discovery tests and dataset helpers |
| `nanodet.util.set_multi_processing` | `(mp_start_method='fork', opencv_num_threads=0, distributed=True)` | Configure multiprocessing and thread counts | Adjusts `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, OpenCV threads, and start method |
| `nanodet.util.stack_batch_img` | `(img_tensors, divisible=0, pad_value=0.0)` | Pad and stack image tensors | Used by training and inference collation |
| `nanodet.model.module.nms.multiclass_nms` | `(multi_bboxes, multi_scores, score_thr, nms_cfg, max_num=-1, score_factors=None)` | Multi-class NMS used by heads | Relies on `torchvision.ops.nms` |
| `nanodet.model.module.nms.batched_nms` | `(boxes, scores, idxs, nms_cfg, class_agnostic=False)` | Batched NMS helper | Used by `multiclass_nms` |
| `nanodet.model.backbone.timm_wrapper.TIMMWrapper` | `(model_name, features_only=True, pretrained=True, checkpoint_path='', in_channels=3, **kwargs)` | Wrap a backbone from `timm` | Raises a runtime error if `timm` is missing |
| `nanodet.trainer.task.TrainingTask` | `(cfg, evaluator=None)` | Lightning module for train/val/test | Owns forward, loss, validation, test, optimizer, and EMA hooks |
| `nanodet.util.logger.Logger` | `(local_rank, save_dir='./', use_tensorboard=True)` | Classic file+console logger | Creates `logs.txt` and optionally TensorBoard logs |
| `nanodet.util.logger.NanoDetLightningLogger` | `(save_dir='./', **kwargs)` | PyTorch Lightning logger | Writes `logs.txt`, `train_cfg.yml`, and TensorBoard scalars |
| `nanodet.model.weight_averager.ExpMovingAverager` | `(decay=0.9998, device=None)` | Exponential moving average of model weights | Used when `model.weight_averager` is configured |

## Common config facts

- `cfg.model.arch.head.num_classes` must match `len(cfg.class_names)` in the training script.
- `cfg.device.gpu_ids == -1` selects the CPU branch in the train/test scripts.
- The demo / export scripts use `cfg.data.val.pipeline` and `cfg.data.val.input_size` for preprocessing.
- `RepVGG` export requires deploy conversion before export or deployment.

## Where to read next

- `references/model-overview.md` for supported model families and config combos.
- `sub-skills/dataset-config/references/configuration.md` for config-field details.
- `sub-skills/training/references/workflows.md` for train/test/checkpoint flows.
- `sub-skills/inference-export/references/workflows.md` for inference and export flows.
