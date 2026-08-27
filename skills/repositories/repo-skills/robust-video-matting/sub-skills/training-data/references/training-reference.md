# Training Reference

## When to read

Read this when constructing RVM training commands, explaining stage schedules,
or debugging `train.py` flags and runtime assumptions.

## Runtime assumptions

`train.py` is a distributed CUDA training launcher. It computes
`world_size = torch.cuda.device_count()` and spawns one `Trainer` process per
GPU. Each trainer initializes an NCCL process group, converts the model to
SyncBatchNorm, wraps it in DDP, and uses AMP by default unless
`--disable-mixed-precision` is set.

Do not treat this script as a CPU smoke test. Use dataset validation and import
checks first, then run carefully scoped training only on an appropriate GPU
machine with data present.

## Main CLI flags

Model and dataset:

- `--model-variant {mobilenetv3,resnet50}`: required.
- `--dataset {videomatte,imagematte}`: required matting dataset branch.

Learning rates:

- `--learning-rate-backbone`: required.
- `--learning-rate-aspp`: required.
- `--learning-rate-decoder`: required.
- `--learning-rate-refiner`: required.

Training settings:

- `--train-hr`: enable high-resolution pass.
- `--resolution-lr`: default `512`.
- `--resolution-hr`: default `2048`.
- `--seq-length-lr`: required.
- `--seq-length-hr`: default `6`.
- `--downsample-ratio`: default `0.25` for high-resolution matting pass.
- `--batch-size-per-gpu`: default `1`.
- `--num-workers`: default `8`.
- `--epoch-start`: default `0`.
- `--epoch-end`: default `16`.

Logging/checkpoints:

- `--log-dir`: required.
- `--log-train-loss-interval`: default `20`.
- `--log-train-images-interval`: default `500`.
- `--checkpoint`: optional restore path.
- `--checkpoint-dir`: required.
- `--checkpoint-save-interval`: default `500`.

Distributed/debug:

- `--distributed-addr`: default `localhost`.
- `--distributed-port`: default `12355`.
- `--disable-progress-bar`.
- `--disable-validation`.
- `--disable-mixed-precision`.

## Official four-stage MobileNetV3 recipe

Stage 1: low-resolution VideoMatte.

```bash
python train.py \
  --model-variant mobilenetv3 \
  --dataset videomatte \
  --resolution-lr 512 \
  --seq-length-lr 15 \
  --learning-rate-backbone 0.0001 \
  --learning-rate-aspp 0.0002 \
  --learning-rate-decoder 0.0002 \
  --learning-rate-refiner 0 \
  --checkpoint-dir checkpoint/stage1 \
  --log-dir log/stage1 \
  --epoch-start 0 \
  --epoch-end 20
```

Stage 2: longer low-resolution sequences from stage 1 checkpoint.

```bash
python train.py \
  --model-variant mobilenetv3 \
  --dataset videomatte \
  --resolution-lr 512 \
  --seq-length-lr 50 \
  --learning-rate-backbone 0.00005 \
  --learning-rate-aspp 0.0001 \
  --learning-rate-decoder 0.0001 \
  --learning-rate-refiner 0 \
  --checkpoint checkpoint/stage1/epoch-19.pth \
  --checkpoint-dir checkpoint/stage2 \
  --log-dir log/stage2 \
  --epoch-start 20 \
  --epoch-end 22
```

Stage 3: high-resolution VideoMatte refinement.

```bash
python train.py \
  --model-variant mobilenetv3 \
  --dataset videomatte \
  --train-hr \
  --resolution-lr 512 \
  --resolution-hr 2048 \
  --seq-length-lr 40 \
  --seq-length-hr 6 \
  --learning-rate-backbone 0.00001 \
  --learning-rate-aspp 0.00001 \
  --learning-rate-decoder 0.00001 \
  --learning-rate-refiner 0.0002 \
  --checkpoint checkpoint/stage2/epoch-21.pth \
  --checkpoint-dir checkpoint/stage3 \
  --log-dir log/stage3 \
  --epoch-start 22 \
  --epoch-end 23
```

Stage 4: high-resolution ImageMatte refinement.

```bash
python train.py \
  --model-variant mobilenetv3 \
  --dataset imagematte \
  --train-hr \
  --resolution-lr 512 \
  --resolution-hr 2048 \
  --seq-length-lr 40 \
  --seq-length-hr 6 \
  --learning-rate-backbone 0.00001 \
  --learning-rate-aspp 0.00001 \
  --learning-rate-decoder 0.00005 \
  --learning-rate-refiner 0.0002 \
  --checkpoint checkpoint/stage3/epoch-22.pth \
  --checkpoint-dir checkpoint/stage4 \
  --log-dir log/stage4 \
  --epoch-start 23 \
  --epoch-end 28
```

## Losses

`matting_loss(pred_fgr, pred_pha, true_fgr, true_pha)` combines alpha L1,
alpha Laplacian, alpha temporal coherence, foreground L1 on nonzero alpha, and
foreground temporal coherence.

`segmentation_loss(pred_seg, true_seg)` is binary cross entropy with logits.
Training alternates between matting samples and person segmentation samples.

## Practical adaptation notes

- Reduce `--num-workers` when dataloaders crash or memory is limited.
- Set a unique `--distributed-port` if multiple trainings run on the same host.
- Use `--disable-validation` only for debugging; validation catches data issues.
- Checkpoint paths are ordinary files; stage commands assume prior stages saved
  the listed checkpoint names.
- `pretrained_backbone=True` in `init_model` can download TorchVision backbone
  weights if not cached.
