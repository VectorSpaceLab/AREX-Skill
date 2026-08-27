# Training and Evaluation Workflows

## Purpose

Read this when you need command patterns for CVNets training, finetuning, resume, or evaluation runs.

## Verified entry points

- `scripts/cvnets_train.py` wraps `main_train.main_worker`.
- `scripts/cvnets_eval.py` wraps `main_eval.main_worker`.
- `scripts/cvnets_eval_det.py` wraps `main_eval.main_worker_detection`.
- `scripts/cvnets_eval_seg.py` wraps `main_eval.main_worker_segmentation`.

## Training pattern

```bash
python sub-skills/training-and-evaluation/scripts/cvnets_train.py \
  --repo-root <repo-root> \
  --common.config-file config/classification/imagenet/resnet.yaml \
  --common.results-loc results
```

Useful additions:

- `--common.resume <checkpoint>` to resume from a checkpoint.
- `--common.finetune <checkpoint>` to load pretrained weights for finetuning.
- `--common.auto-resume` to resume from the last checkpoint in the run directory.
- `--common.override-kwargs key=value ...` for small one-off edits.
- `--ddp.rank`, `--ddp.world-size`, `--ddp.dist-url`, and `--ddp.backend` for distributed launches.
- `--common.mixed-precision` and `--common.channels-last` when the model and backend support them.

## Generic evaluation pattern

```bash
python sub-skills/training-and-evaluation/scripts/cvnets_eval.py \
  --repo-root <repo-root> \
  --common.config-file config/classification/imagenet/resnet.yaml \
  --common.results-loc results \
  --model.classification.pretrained <weights>
```

## Detection evaluation pattern

```bash
python sub-skills/training-and-evaluation/scripts/cvnets_eval_det.py \
  --repo-root <repo-root> \
  --common.config-file config/detection/ssd_coco/resnet.yaml \
  --common.results-loc results \
  --model.detection.pretrained <weights> \
  --model.detection.n-classes 81 \
  --evaluation.detection.resize-input-images \
  --evaluation.detection.mode validation_set
```

For single-image or image-folder evaluation, provide `--evaluation.detection.path` and the confidence threshold used by the model head.

## Segmentation evaluation pattern

```bash
python sub-skills/training-and-evaluation/scripts/cvnets_eval_seg.py \
  --repo-root <repo-root> \
  --common.config-file config/segmentation/ade20k/deeplabv3_mobilenetv2.yaml \
  --common.results-loc results \
  --model.segmentation.pretrained <weights> \
  --model.segmentation.n-classes <classes> \
  --evaluation.segmentation.resize-input-images \
  --evaluation.segmentation.mode validation_set
```

For single-image or folder evaluation, add the save-mask and overlay flags only when you want image outputs.

## Resume and finetuning notes

- `common.resume` and `common.auto-resume` are for continuing the same training run.
- `common.finetune` is for loading weights into a fresh run.
- For classification finetuning from ImageNet checkpoints, the config often also needs `model.classification.finetune_pretrained_model=false` on evaluation-only passes.
- If the checkpoint was trained for a different number of classes, fix the task head before retrying.

## DDP notes

- `main_train.py` uses multi-GPU spawn when the visible GPU count is greater than one.
- The repo adjusts per-process dataset workers and batch sizes based on the visible GPU count.
- If the process count or rank values do not match the visible GPUs, fix the `--ddp.*` arguments before retrying.
- For CPU smoke checks, keep the GPU count at zero and disable mixed precision.
