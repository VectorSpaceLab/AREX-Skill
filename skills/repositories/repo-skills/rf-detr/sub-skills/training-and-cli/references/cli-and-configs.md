# Lightning CLI and YAML configs

The public console script is `rfdetr -> rfdetr.cli:main`, which runs the RF-DETR Lightning CLI. Install CLI dependencies with:

```bash
pip install "rfdetr[train,cli]"
```

Use `pip install "rfdetr[train,cli,augment,loggers]"` when a YAML uses custom augmentation or W&B/MLflow/TensorBoard extras.

## Commands

The CLI exposes Lightning subcommands:

```bash
rfdetr --help
rfdetr fit --help
rfdetr validate --help
rfdetr test --help
rfdetr predict --help
```

`fit` trains. `validate` and `test` run dataset-backed evaluation with a Lightning checkpoint. `predict` uses the datamodule pipeline and is not the arbitrary-image `RFDETR.predict()` API.

## YAML structure

```yaml
model:
  model_config:
    class_path: rfdetr.config.RFDETRSmallConfig
    init_args:
      num_classes: 3
  train_config:
    class_path: rfdetr.config.TrainConfig
    init_args:
      dataset_file: roboflow
      dataset_dir: data/my_dataset
      output_dir: outputs/rfdetr-small
      epochs: 100
      batch_size: 4
      grad_accum_steps: 4
      num_workers: 4
      tensorboard: true
```

`RFDETRCli` links `model.model_config` to `data.model_config` and `model.train_config` to `data.train_config` at parse time. Define each config once under `model`; the datamodule receives the linked values.

Run a bundled example from this sub-skill tree:

```bash
rfdetr fit --config references/configs/rfdetr_small.yaml
```

Override nested config values with jsonargparse/Lightning dotted arguments:

```bash
rfdetr fit --config references/configs/rfdetr_small.yaml \
  --model.train_config.init_args.dataset_dir data/my_dataset \
  --model.train_config.init_args.output_dir outputs/run2 \
  --trainer.devices 4
```

If a downstream project ships its own YAML, inspect it first:

```bash
python scripts/inspect_training_config.py --config path/to/config.yaml
```

The inspector imports config/CLI surfaces and instantiates Pydantic config objects only. It never instantiates model wrappers, downloads pretrained weights, creates a Trainer, or starts Lightning.

## Config class selection

| Task | `model_config.class_path` | `train_config.class_path` |
| --- | --- | --- |
| Detection | `rfdetr.config.RFDETRSmallConfig` (or another released sized detection config) | `rfdetr.config.TrainConfig` |
| Segmentation | `rfdetr.config.RFDETRSegSmallConfig` (or another released sized segmentation config) | `rfdetr.config.SegmentationTrainConfig` |
| Keypoint preview | `rfdetr.config.RFDETRKeypointPreviewConfig` | `rfdetr.config.KeypointTrainConfig` |

Prefer `RFDETRSmallConfig` for new detection examples. Avoid new `RFDETRBaseConfig` examples unless maintaining legacy compatibility. Segmentation should use sized `RFDETRSeg*Config` variants, not segmentation preview.

## Architecture fields vs train fields

Put architecture fields under `model_config`:

- `num_classes`
- `num_keypoints_per_class`
- `resolution`
- `gradient_checkpointing`
- `pretrain_weights`
- `patch_size`, `num_windows`, and other architecture-only fields

Put runtime/training fields under `train_config`:

- `dataset_file`, `dataset_dir`, `output_dir`, `epochs`
- `batch_size`, `grad_accum_steps`, `num_workers`
- `lr`, `lr_encoder`, `optimizer`, `lr_scheduler`
- `resume`, `checkpoint_interval`, `skip_best_epochs`
- `augmentation_backend`, `aug_config`, `scale_jitter`
- `tensorboard`, `wandb`, `mlflow`, `project`, `run`
- `accelerator`, `devices`, `strategy`, `num_nodes`

`resolution` must be divisible by the model's block size (`patch_size * num_windows`). The CLI path does not resolve `batch_size="auto"`; replace it with a concrete integer.

## Keypoint CLI example

```yaml
model:
  model_config:
    class_path: rfdetr.config.RFDETRKeypointPreviewConfig
    init_args:
      num_classes: 1
      num_keypoints_per_class: [17]
  train_config:
    class_path: rfdetr.config.KeypointTrainConfig
    init_args:
      dataset_file: roboflow
      dataset_dir: data/my_pose_dataset
      output_dir: outputs/keypoint
      epochs: 50
      batch_size: 2
      grad_accum_steps: 8
      keypoint_flip_pairs: [1, 2, 3, 4]
      run_test: false
```

For YOLO pose, use `dataset_file: yolo` or `roboflow` auto-detection and ensure `data.yaml` declares `kpt_shape`. Set `augmentation_backend: cpu` or `albumentations`; do not set `kornia` for keypoint training.

## validate, test, and predict

The CLI uses Lightning's `--ckpt_path` convention:

```bash
rfdetr validate --config references/configs/rfdetr_small.yaml --ckpt_path outputs/run/last.ckpt
rfdetr test --config references/configs/rfdetr_small.yaml --ckpt_path outputs/run/last.ckpt
rfdetr predict --config references/configs/rfdetr_small.yaml --ckpt_path outputs/run/last.ckpt
```

Use full `.ckpt` files for Lightning loop-state restoration. Lightweight `.pth` best checkpoints are usually better loaded through the Python API for inference or used as `pretrain_weights` for a fresh fine-tune. CLI `predict` runs the validation-style datamodule pipeline; use the inference sibling sub-skill for arbitrary files, video, or `supervision` outputs.

## Multi-GPU CLI pattern

For a CLI launch under `torchrun`, pass Trainer device/strategy overrides:

```bash
torchrun --nproc_per_node=4 -m rfdetr fit \
  --config references/configs/rfdetr_small.yaml \
  --trainer.devices 4 \
  --trainer.strategy ddp
```

The Trainer default is one device. Effective global batch is `batch_size * grad_accum_steps * num_gpus`; adjust accumulation when changing GPU count. For keypoints, prefer DDP with `grad_accum_steps=1` on multi-GPU.

## Bundled example configs

Bundled, adapted examples are available inside this sub-skill tree:

- [references/configs/rfdetr_small.yaml](configs/rfdetr_small.yaml)
- [references/configs/rfdetr_seg_small.yaml](configs/rfdetr_seg_small.yaml)
- [references/configs/rfdetr_keypoint_preview.yaml](configs/rfdetr_keypoint_preview.yaml)

Copy one into the user's working project or pass its path to `rfdetr`; replace only public dataset/output placeholders and task-specific schema.

## CLI checks

```bash
python scripts/inspect_training_config.py
python scripts/inspect_training_config.py --config references/configs/rfdetr_small.yaml --strict
python scripts/validate_dataset_layout.py data/my_dataset --task auto
```

TensorBoard is on by default in `TrainConfig`, but missing logger packages result in warning and CSV-only logging. W&B/MLflow require credentials or tracking configuration outside RF-DETR. `clearml: true` is unsupported and raises `NotImplementedError`; use the ClearML SDK workaround instead.
