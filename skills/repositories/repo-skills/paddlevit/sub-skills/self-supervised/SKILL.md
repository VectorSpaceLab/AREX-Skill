---
name: self-supervised
description: "Use for PaddleViT's DINO self-supervised vision-transformer
  pretraining, multi-crop data contracts, teacher/student configuration, single-
  or multi-GPU launch planning, checkpoint/resume handling, and optional
  PyTorch-to-Paddle weight-porting boundaries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PaddleViT DINO self-supervised learning

Use this sub-skill when a task names `self_supervised_learning/dino`, DINO
pretraining, multi-crop augmentation, a DINO teacher/student checkpoint, or
porting a DINO ViT backbone into Paddle. It is an operating guide for the
PaddleViT checkout, not a promise that every released script is runnable as-is.
Keep the source checkout and this skill's evidence boundary explicit.

## Applicability and hard boundaries

- The supported end-to-end data path is the ImageNet2012-style path consumed by
  `ImageNet2012Dataset`: `DATA.DATA_PATH/train_list.txt` and
  `DATA.DATA_PATH/val_list.txt`, with image paths relative to that directory.
  Each line is `<relative-image-path> <integer-label>`; labels are ignored by
  DINO but are still required by the dataset reader.
- Actual DINO training needs `DATA.DATASET=imagenet2012`. The CIFAR branches in
  `datasets.py` return a single transformed tensor and therefore do not satisfy
  the multi-crop contract used by `main_*_gpu.py`.
- One training sample is transformed into two global views at
  `DATA.IMAGE_SIZE` and `DATA.LOCAL_CROPS_NUMBER` local views at
  `DATA.SMALL_CROP_IMAGE_SIZE`. Defaults are 2 global + 10 local views, 224/96
  pixels, global scale `[0.25, 1.0]`, and local scale `[0.05, 0.25]`.
- The teacher receives only `images[:2]`; the student receives all crops. Crop
  tensors must be batched, normalized with the configured ImageNet mean/std,
  and grouped by spatial size because `MultiCropWrapper` groups consecutive
  equal-width crops.
- This skill does not authorize downloading ImageNet, checkpoints, or external
  repositories, nor starting benchmark-scale or long-running pretraining.
  Prefer config checks, import checks, synthetic tensors, and a bounded one-step
  smoke. State the required dataset, GPU count, wall-time, and output directory
  before proposing a real run.
- `torch`, `timm`, and the PyTorch DINO hub model are optional porting
  dependencies. They are not required for Paddle DINO training and are absent
  from the inspected environment; do not install or fetch them implicitly.

## Evidence and source map

Primary evidence is the pinned checkout's
`self_supervised_learning/dino/{README.md,config.py,datasets.py,transformer.py,utils.py,main_dino_single_gpu.py,main_dino_multi_gpu.py,run_train_multi.sh}`
and `self_supervised_learning/dino/port_weights/load_pytorch_weights.py`.
Cross-cutting launch, configuration, AMP, and porting guidance is in
`docs/paddlevit-{config,multi-gpu,amp,port-weights}.md`. The source is an
older Paddle implementation (Paddle 2.1-era assumptions); use the bundled
scripts for bounded checks and treat source defects below as evidence, not as
silent corrections.

## Configuration procedure

1. Start from `self_supervised_learning/dino/configs/vit_small_patch16_224.yaml`
   or `vit_base_patch16_224.yaml`; pass it with `-cfg` from the DINO directory.
   YAML is merged into the defaults in `config.py`, then CLI values override
   selected fields. Use the same effective config for model construction and
   record it with the run.
2. Check the coupled dimensions before launch:
   `IMAGE_SIZE % PATCH_SIZE == 0`, `SMALL_CROP_IMAGE_SIZE % PATCH_SIZE == 0`,
   `EMBED_DIM % NUM_HEADS == 0`, positive `OUT_DIM`, two ordered crop-scale
   bounds in `(0, 1]`, and `LOCAL_CROPS_NUMBER >= 1`. Run
   `scripts/check_dino_config.py --config <yaml>`; it is read-only.
3. Preserve the DINO defaults unless a bounded experiment justifies a change:
   AdamW, cosine LR/weight-decay schedules, teacher momentum warming toward 1,
   teacher temperature warmup, `FREEZE_LAST_LAYER`, and `OUT_DIM=65536`.
   Note that the README says weight-decay scheduling was not supported in the
   2022 release, while the current code computes a schedule; verify the actual
   checkout before relying on that behavior.
4. Set `DATA.BATCH_SIZE` per GPU, not global batch size. Scale effective batch
   size and learning rate deliberately when changing GPU count; the source
   does not automatically apply the documented linear-LR convention.
5. Treat `MODEL.PRETRAINED` as a backbone/model-state input only after checking
   the exact state-dict shape and naming. A DINO run needs student/teacher/head
   compatibility, not merely a classification checkpoint.

See [references/configuration.md](references/configuration.md) for the field
contract and [scripts/check_dino_config.py](scripts/check_dino_config.py) for
safe validation.

## Teacher/student and multi-crop procedure

The intended construction is two ViTs with shared initial state: the student
uses configured stochastic depth and the teacher is rebuilt with `DROPPATH=0`.
Each is wrapped by `MultiCropWrapper` and a `DINOHead`; teacher parameters have
`stop_gradient=True`. The student is optimized; the teacher is updated after
each step by EMA using `MOMENTUM_TEACHER`'s cosine schedule. `DINOLoss` sharpens
and centers the teacher output, compares the two teacher global views against
all nonmatching student views, and maintains a center buffer.

For a synthetic check, use two `[B,3,32,32]` global tensors and two or more
`[B,3,16,16]` local tensors with a tiny ViT config. Do not infer ImageNet
accuracy from this check. Run:

```bash
python scripts/dino_model_smoke.py --help
python scripts/dino_model_smoke.py --repo-root /path/to/PaddleViT --device cpu
# On a prepared CUDA host, use --device gpu:0 (no dataset or download).
```

A successful bounded smoke should show model construction, crop shapes, a
student/teacher forward, finite DINO logits/loss, and no parameter update on
the teacher. If the checkout's wrapper/API fails, retain the diagnostic and do
not claim training compatibility; do not hide it by downloading PyTorch.

## Launch procedure and backend gates

### Single GPU

Use the single-process entrypoint only after config and smoke checks:

```bash
CUDA_VISIBLE_DEVICES=0 python main_dino_single_gpu.py \
  -cfg=./configs/vit_small_patch16_224.yaml \
  -dataset=imagenet2012 -batch_size=32 \
  -data_path=/dataset/imagenet -output=./output -amp
```

`-batch_size` is per GPU. AMP uses `paddle.amp.auto_cast` and `GradScaler`;
repository docs limit FP16 AMP claims to NVIDIA Ampere, Volta, and Turing.
Require a CUDA Paddle build and a successful CUDA tensor/layer smoke before
using `-amp`. CPU is suitable for import/tiny checks only, not this training
claim.

### Single-node multi GPU

The source launcher uses `paddle.distributed.spawn`, initializes one worker per
visible GPU, wraps models in `paddle.DataParallel`, uses
`DistributedBatchSampler`, and all-reduces loss/center statistics. Use an
explicit device list and `-ngpus` matching it; a distributed run requires NCCL
and multiple usable CUDA devices:

```bash
CUDA_VISIBLE_DEVICES=0,1 python main_dino_multi_gpu.py \
  -ngpus=2 -cfg=./configs/vit_small_patch16_224.yaml \
  -dataset=imagenet2012 -batch_size=16 -data_path=/dataset/imagenet -amp
```

The repository's `run_train_multi.sh` is an eight-GPU, long-running ImageNet
launcher and is reference-only. Do not execute it during skill use. Validate
world size, rank, sampler partitioning, and rendezvous in a short controlled
job before any real run. Do not call one-GPU execution a multi-GPU pass.

### Known source hazards to check before a real launch

The inspected scripts contain apparent defects that a user must resolve or
patch in a controlled copy and then re-run the bounded checks for:

- single-GPU `train` returns two values but `main` unpacks three; later code
  references `local_logger`, `model`, and `scheduler` inconsistently;
- both entrypoints contain `params_gropus`/`params_groups` inconsistency;
- pretrain/resume code references `model` instead of the student/teacher model;
- resume and save paths have inconsistent DINO-loss suffixes (`._dino_loss`,
  `_dino_loss.pdparams`, and `_dino_loss.pdprams`);
- the config's `MODEL.NORM_LAST_LAYER` is not consistently wired into the
  hard-coded head construction;
- `ACCUM_ITER` is accepted but the shown loop still clears and steps every
  batch.

These are not permission to perform an unreviewed rewrite. Record the exact
checkout, patch, effective config, and smoke result. If the task is only to
inspect or plan, stop at the hazard report.

## Checkpoints and resume

The intended save prefix is under `SAVE/train-<timestamp>/` and includes a
`.pdparams` model state, `.pdopt` optimizer state, and a DINO-loss state. The
teacher is the meaningful exported representation in the multi-GPU saver; the
source's suffix typo means you must inspect actual files rather than guessing.
Use `TRAIN.LAST_EPOCH` consistently with the checkpoint's epoch and preserve
optimizer state, teacher center, temperature schedule, and effective config.
A model-only load is not an exact resume. Before resuming, assert that all
three expected artifacts exist, compare parameter names/shapes, and make a
copy or use a new output directory. Never overwrite a checkpoint silently.

## Optional PyTorch weight porting

`port_weights/load_pytorch_weights.py` is a separate, CPU-oriented conversion
example. It imports `torch`, loads `facebookresearch/dino:main` via
`torch.hub`, maps the ViT backbone names, transposes 2-D linear weights, and
checks a batched output with `np.allclose`. It does not establish a full DINO
student/teacher/head conversion or checkpoint resume. Keep this route optional:
only use an approved isolated environment with a local PyTorch checkpoint and
explicit source/target model specifications. Manually inspect parameters and
buffers, preserve non-linear 2-D tensors without transpose, compare batched
outputs, and save a new `.pdparams`; never fetch a hub model as an implicit
step. The current environment has no torch/timm, so this path is unverified.

## Recovery and stop conditions

- Missing `train_list.txt` or wrong image-root layout: stop and report the
  expected layout; do not download or synthesize ImageNet silently.
- Crop count/shape mismatch or non-finite loss: stop before long training;
  verify transform order, `LOCAL_CROPS_NUMBER + 2`, normalization, output
  dimension, teacher temperature, and model state.
- CUDA/AMP failure: rerun the CPU import/tiny smoke, then the CUDA preparation
  probe; mark GPU-specific behavior blocked if CUDA or the required device
  is unavailable.
- Distributed hang or unequal ranks: terminate the bounded job, check visible
  devices, `-ngpus`, NCCL/rendezvous, and sampler/world-size setup. Do not
  retry indefinitely.
- Checkpoint mismatch: start a new output directory and use a shape/name report;
  do not force-load incompatible heads or silently discard the teacher center.

## Difficult synthetic usability cases

1. **Crop-contract and teacher-EMA case:** build a tiny ViT with two 32x32
   global views and three 16x16 local views, run one finite DINO step, assert
   teacher outputs use two views, student outputs use five, teacher parameters
   remain gradient-free, and EMA changes the teacher without changing crop
   counts. No filesystem dataset or network may be used.
2. **Resume/port boundary case:** provide a temporary checkpoint prefix with a
   model state, optimizer state, and deliberately misspelled loss suffix, then
   ask the agent to diagnose whether it is an exact resume and to produce a
   non-destructive repair plan. Separately provide a fake PyTorch state mapping
   with one transposed linear tensor; the expected result is a blocked optional
   port report when torch is unavailable, not an install or hub download.

## Handoff checklist

Report the source commit, effective YAML/CLI overrides, dataset layout check,
backend/device probe, smoke command and result, launch mode, per-GPU batch,
AMP/distributed assumptions, checkpoint prefix and suffixes, patches applied (if
any), and unresolved source hazards. Do not claim ImageNet pretraining or
multi-GPU success from a synthetic smoke.

## Bundled references

- [workflows.md](references/workflows.md) — bounded checks, launch templates,
  checkpoint flow, and backend boundaries.
- [configuration.md](references/configuration.md) — effective fields and
  invariants.
- [troubleshooting.md](references/troubleshooting.md) — source-specific
  failures and recovery decisions.
