# Supervised Workflows

## Train from scratch

Template:

```bash
torchrun --nproc_per_node <gpus> main.py \
  --cfg <config.yaml> \
  --data-path <imagenet-root> \
  --batch-size <per-gpu-batch> \
  --output <output-root> \
  --tag <run-name>
```

Use `--zip --cache-mode part` when the data root uses zipped ImageNet maps.

## Evaluate a checkpoint

```bash
torchrun --nproc_per_node 1 main.py \
  --eval \
  --cfg <config.yaml> \
  --resume <checkpoint.pth> \
  --data-path <imagenet-root>
```

Use `--resume` for evaluation because the checkpoint should contain a `model` state dict in the repo's checkpoint format.

## Fine-tune from a pretrained checkpoint

```bash
torchrun --nproc_per_node <gpus> main.py \
  --cfg <fine-tune-config.yaml> \
  --pretrained <pretrained-checkpoint.pth> \
  --data-path <imagenet-root> \
  --batch-size <per-gpu-batch> \
  --accumulation-steps <steps> \
  --use-checkpoint
```

For 22K-to-1K fine-tuning, choose a config whose filename includes `22kto1k` or `ft` and use `data-and-checkpoints` to understand classifier-head remapping.

## Throughput

```bash
torchrun --nproc_per_node 1 main.py \
  --cfg <config.yaml> \
  --data-path <imagenet-root> \
  --batch-size 64 \
  --throughput \
  --disable_amp
```

Throughput is a benchmark-style workflow. It requires a working GPU/data setup and should not be used as a smoke test.

## Config overrides

Append `--opts KEY VALUE ...` after ordinary flags. Useful examples:

```bash
--opts TRAIN.EPOCHS 100 TRAIN.WARMUP_EPOCHS 5
--opts DATA.IMG_SIZE 384 MODEL.SWIN.WINDOW_SIZE 12
```

Validate complex overrides before training with the root `scripts/inspect_swin_config.py` helper.
