# DAMO-YOLO training troubleshooting

Use this when a DAMO-YOLO training, evaluation, fine-tuning, or distillation workflow fails. It focuses on bundled train/eval launchers, installed `damo` APIs, `damo.dataset` behavior, config files, and distributed CUDA setup.

## CUDA, NCCL, and distributed launch

| Symptom | Likely cause | Fix |
|---|---|---|
| `RuntimeError: CUDA error: invalid device ordinal` or failure in `torch.cuda.set_device(local_rank)` | `--gpus` exceeds visible GPUs, or `CUDA_VISIBLE_DEVICES` hides devices. | Set `--gpus` to the count of visible GPUs. For one GPU, still use the distributed launcher with `--gpus 1`. |
| `Distributed package doesn't have NCCL built in`, `NCCL error`, or hang in `init_process_group` | CUDA/NCCL PyTorch mismatch, bad network env, or launched without distributed env vars. | Use a CUDA-enabled PyTorch build; launch through `scripts/launch_train.sh` or `scripts/launch_eval.sh`; choose a free `--master-port`; start with one node/one GPU to isolate. |
| `Address already in use` | Port collision. | Pass a different `--master-port`, e.g. `29503`. |
| `unrecognized arguments: --local-rank=...` | Older source launchers only parsed `--local_rank`. | The bundled entry points accept both spellings; use them instead of repo-local launch scripts when possible. |
| Logs appear only from rank 0 or are duplicated | Distributed logging behavior. | Check `cfg.miscs.output_dir/cfg.miscs.exp_name`; rank 0 owns directory creation and most persistent outputs. |

## Batch size and dataloader assertions

Failure signal:

```text
training_imgs_per_batch (<B>) must be divisible by the number of GPUs (<N>) used.
```

Cause: `build_dataloader()` asserts `batch_size % get_world_size() == 0` for both train and eval loaders.

Fix:

- For training, edit `self.train.batch_size` so it is divisible by `--gpus`.
- For evaluation, edit `self.test.batch_size` so it is divisible by eval GPU count.
- Re-run `scripts/launch_train.sh --dry-run` or `scripts/launch_eval.sh --dry-run` after config changes.

## Missing dataset or annotation files

| Symptom | Likely cause | Fix |
|---|---|---|
| `KeyError: '<dataset_name>'` from `DatasetCatalog.DATASETS[name]` | Config uses a dataset name missing from the active catalog. | Add the dataset entry or override `get_data()` in the config. |
| `RuntimeError: Only support coco format dataset now!` | Dataset name does not contain `coco`. | Rename entries such as `my_train_coco` and `my_val_coco`, or override `get_data()`. |
| `FileNotFoundError` for annotation JSON or images | Wrong `DATA_DIR`, `img_dir`, `ann_file`, workdir, symlink, or `file_name` layout. | Check catalog paths, relative path root, and annotation `images[].file_name`. Run `validate_coco_config.py --check-images 5`. |
| `ModuleNotFoundError: pycocotools` or COCO import errors | COCO dependencies missing. | Install DAMO-YOLO runtime requirements plus `pycocotools` in the active environment. |

## Class-name and head mismatches

| Symptom | Likely cause | Fix |
|---|---|---|
| `AssertionError: plz provide class_names` | `cfg.dataset.class_names` is `None`. | Set `self.dataset.class_names = [...]` in the config. |
| `KeyError` in `self.contiguous_class2id[self.ori_id2class[c]]` | Annotation category name is not present in `class_names`. | Make annotation `categories[].name` and config `class_names` match exactly. |
| Checkpoint load size mismatch for detection head | `model.head['num_classes']` differs from checkpoint head and loader is strict. | Use `finetune_path` for adaptation when supported, or choose a checkpoint/config with matching class count. Use `resume_path` only for same architecture/classes. |
| Evaluation produces labels in unexpected order | `class_names` order changed between training and eval. | Use the same class-name order for training, eval, and downstream interpretation. |

## Checkpoint path and checkpoint format problems

| Symptom | Likely cause | Fix |
|---|---|---|
| `torch.load(None, ...)` or file-not-found for eval | Missing `--ckpt` or bad path. | Pass a local `.pth` checkpoint to eval. |
| `KeyError: 'model'` | Checkpoint is not a DAMO-YOLO training/eval checkpoint dict. | Use a DAMO-YOLO PyTorch checkpoint containing `model`, or adapt the loader for a raw state dict. |
| Strict load errors during resume | Config architecture/class count changed since the checkpoint. | Resume only with the same config family; use fine-tune for dataset/class changes. |
| `KeyError: 'optimizer'` or bad epoch when resuming | Checkpoint lacks training state. | Use fine-tune for model-only weights, or resume from a checkpoint saved by `Trainer.save_ckpt()`. |
| Distillation resume complains about `feature_loss` | Resuming a distillation run from a non-distillation checkpoint, or vice versa. | Match the distillation mode and checkpoint type. |

## Config key mismatches after custom edits

- `dataset.data_dir` is not used by the base `get_data()` path lookup; edit `DatasetCatalog.DATA_DIR`, dataset entries, or override `get_data()`.
- Dotted CLI overrides such as `train.batch_size 16` are not reliable in this repo because `Config.merge()` only updates exact top-level attributes.
- The source eval parser accepts `--conf`, `--nms`, `--tsize`, `--seed`, and `--test`, but this version does not visibly apply them. Edit `model.head['nms_conf_thre']`, `model.head['nms_iou_thre']`, `test.augment.transform.image_max_range`, and `dataset.val_ann` in the config.
- Config files may read TinyNAS structure text through relative paths. Use `--workdir` with bundled scripts so those paths resolve from the intended user-owned directory.

## Distillation-specific failures

| Symptom | Likely cause | Fix |
|---|---|---|
| Teacher checkpoint file error | `--tea_ckpt` missing or wrong. | Provide a local teacher detector checkpoint. |
| Teacher config import/load error | `--tea_config` missing, wrong path, or incompatible config. | Parse the teacher config with `parse_config()` before launching. |
| CUDA out of memory | Student + teacher + feature loss exceed memory. | Reduce batch size, GPU count per process layout, image size, or model size. |
| Class/head mismatch | Teacher checkpoint does not match teacher config or target classes. | Use teacher assets trained for the same class set, or retrain/fine-tune teacher first. |

## Install/build isolation failures

DAMO-YOLO's setup file imports `torch` during setup. If editable installation fails with `ModuleNotFoundError: No module named 'torch'` inside an isolated build environment, install a compatible PyTorch build first and retry with build isolation disabled in a private environment:

```bash
python -m pip install torch torchvision
python -m pip install -e /path/to/damo-yolo-source --no-build-isolation
```

Do not put environment-specific paths or private prefixes into shared docs or configs.

## Seed and reproducibility notes

- `Trainer.__init__` has `set_seed(cfg.miscs.seed)` commented out in this repo version, so `cfg.miscs.seed` alone may not make training deterministic.
- The eval source parses `--seed` but does not visibly apply it. If deterministic evaluation is required, add explicit seeding in the target workflow and document the patch.

## When to route elsewhere

- Image/video/camera demo failures belong to inference/demo coverage, not this training sub-skill.
- ONNX/TensorRT export, TensorRT evaluation, and partial quantization belong to deployment/export coverage. TensorRT is an optional deployment stack, not a training dependency.
