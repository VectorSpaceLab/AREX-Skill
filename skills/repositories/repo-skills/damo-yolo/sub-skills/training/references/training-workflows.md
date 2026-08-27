# DAMO-YOLO training and evaluation workflows

This reference distills DAMO-YOLO's train/eval/distillation behavior into bundled, self-contained launchers. The bundled scripts import the installed `damo` package and do not call repo-local `tools/train.py` or `tools/eval.py`. Users still provide their own config, checkpoint, dataset, and any directory needed to resolve relative paths inside those files.

## Runtime shape

- Training and evaluation are CUDA/NCCL workflows. The source implementation calls `torch.cuda.set_device(local_rank)` and initializes `torch.distributed` with `backend='nccl'` before building data or models.
- The bundled launchers use `python -m torch.distributed.run` and bundled Python entry points that accept both `--local_rank` and `--local-rank` conventions.
- Single-GPU evaluation still uses distributed launch with `--gpus 1`.
- Verified package APIs include `parse_config(config_file)`, `build_local_model(config, device)`, `build_dataset(cfg, ann_files, is_train=True, mosaic_mixup=None)`, `build_dataloader(...)`, and `Trainer(cfg, args, tea_cfg=None, is_train=True)`.

## Choose train, fine-tune, resume, eval, or distill

| Task | Bundled entry point | Required state |
|---|---|---|
| Reproduce COCO training | `scripts/launch_train.sh --config <config.py>` | COCO dataset mapping, class list for COCO, batch size divisible by GPU count. |
| Fine-tune on custom data | `scripts/launch_train.sh --config <custom_config.py>` | Set custom `train_ann`, `val_ann`, `class_names`, `model.head['num_classes']`, and `train.finetune_path`. |
| Resume interrupted training | `scripts/launch_train.sh --config <same_config.py>` | Set only `train.resume_path` to a DAMO-YOLO training checkpoint containing `model`, `optimizer`, and `epoch`. |
| Evaluate a checkpoint | `scripts/launch_eval.sh --config <config.py> --ckpt <checkpoint.pth>` | Eval config class count must match checkpoint head; validation dataset must exist. |
| Distillation | `scripts/launch_train.sh --config <student.py> --tea-config <teacher.py> --tea-ckpt <teacher.pth>` | Teacher config/checkpoint must be compatible with the teacher model; expect high GPU/memory cost. |

Use `--workdir <path>` only when a config performs relative file reads, for example TinyNAS structure text files or dataset entries relative to a specific project directory. The workdir is a user-provided runtime directory, not a generated-skill dependency.

## COCO training from scratch

```bash
sub-skills/training/scripts/launch_train.sh \
  --config /path/to/damoyolo_tinynasL25_S.py \
  --workdir /path/used/by/config-relative-assets \
  --gpus 8 \
  --master-port 29500
```

The launcher validates the config import, dataset mapping, visible CUDA device count, and NCCL availability before launching. If the dataset is intentionally absent during planning, use `--dry-run` only after providing a config whose catalog entries can be resolved.

## Fine-tuning on a custom COCO dataset

1. Create a custom config from the nearest model-size recipe and make it self-contained for the working directory you will pass with `--workdir`.
2. Add dataset mapping and class names as described in [Custom COCO dataset setup](custom-coco-datasets.md) and [Config editing guide](config-editing.md).
3. Set a detector checkpoint for warm-starting:

```python
self.train.finetune_path = 'checkpoints/damoyolo_pretrained.pth'
self.train.resume_path = None
```

4. Validate then train:

```bash
sub-skills/training/scripts/validate_coco_config.py \
  --config /path/to/my_damoyolo_custom.py \
  --workdir /path/used/by/config-relative-assets \
  --split both --check-images 3

sub-skills/training/scripts/launch_train.sh \
  --config /path/to/my_damoyolo_custom.py \
  --workdir /path/used/by/config-relative-assets \
  --gpus 4 \
  --master-port 29501
```

`finetune_path` uses `model.load_pretrain_detector()` and starts from epoch 0. It is the right choice when the dataset or class count changed.

## Resume an interrupted training run

Set only `resume_path` in the same config family used for the interrupted run:

```python
self.train.finetune_path = None
self.train.resume_path = 'workdirs/<exp_name>/latest_ckpt.pth'
```

Then launch training normally. Resume uses strict `model.load_state_dict(ckpt['model'])`, restores `ckpt['optimizer']`, and sets `start_epoch` from `ckpt['epoch']`. Do not use resume for a checkpoint whose head shape differs from the current config.

## Evaluation

```bash
sub-skills/training/scripts/launch_eval.sh \
  --config /path/to/damoyolo_tinynasL25_S.py \
  --workdir /path/used/by/config-relative-assets \
  --ckpt /path/to/damoyolo_tinynasL25_S_456.pth \
  --gpus 1 \
  --master-port 29502 \
  --fuse
```

Evaluation loads checkpoint weights, strips the text `module` from checkpoint keys, switches `RepConv` layers to deploy mode, builds DDP, then runs COCO-style inference for `cfg.dataset.val_ann`. Output goes under `cfg.miscs.output_dir`, including an `inference/<dataset-name>` subdirectory.

Caveat: the source eval parser accepts `--conf`, `--nms`, `--tsize`, `--seed`, and `--test`, but this repo version does not visibly apply them except `--fuse`. For reliable threshold/size changes, edit these config keys instead:

```python
self.model.head['nms_conf_thre'] = 0.05
self.model.head['nms_iou_thre'] = 0.7
self.test.augment.transform.image_max_range = (640, 640)
self.dataset.val_ann = ('my_val_coco',)
```

## Distillation

The distillation source snippet is intentionally reference-only because it assumes external teacher checkpoints and a large multi-GPU run. When the user explicitly has the teacher assets, use the bundled training launcher:

```bash
sub-skills/training/scripts/launch_train.sh \
  --config /path/to/student_custom.py \
  --workdir /path/used/by/config-relative-assets \
  --gpus 8 \
  --master-port 29503 \
  --tea-config /path/to/teacher_custom.py \
  --tea-ckpt /path/to/teacher_detector.pth
```

What happens internally:

- The bundled `train_entrypoint.py` parses `--tea_config` and `--tea_ckpt` and then calls DAMO-YOLO's installed `Trainer`.
- `Trainer` builds the student from `cfg`, builds the teacher from `tea_cfg`, loads teacher weights through `tea_model.load_pretrain_detector(args.tea_ckpt)`, and adds `FeatureLoss(..., distiller='cwd')` to the student detection loss.
- Distillation sets `grad_clip = 30` and saves `feature_loss` state in training checkpoints.

Use distillation only when teacher config/checkpoint, class set, and GPU memory budget are realistic.
