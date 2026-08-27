# SimMIM Workflows

## Pretraining

Use the pretraining script and a `simmim_pretrain__...` config:

```bash
torchrun --nproc_per_node <gpus> main_simmim_pt.py \
  --cfg <simmim-pretrain-config.yaml> \
  --data-path <imagenet-root>/train \
  --batch-size <per-gpu-batch> \
  --output <output-root> \
  --tag <run-name>
```

The pretraining loader expects a training image folder and creates masks with `MaskGenerator`.

## Fine-tuning

Use the fine-tuning script and a `simmim_finetune__...` config:

```bash
torchrun --nproc_per_node <gpus> main_simmim_ft.py \
  --cfg <simmim-finetune-config.yaml> \
  --data-path <imagenet-root> \
  --pretrained <simmim-pretrained-checkpoint.pth> \
  --batch-size <per-gpu-batch>
```

Fine-tuning uses the standard ImageNet train/val folder layout.

## Evaluation

```bash
torchrun --nproc_per_node 1 main_simmim_ft.py \
  --eval \
  --cfg <simmim-finetune-config.yaml> \
  --resume <fine-tuned-checkpoint.pth> \
  --data-path <imagenet-root>
```

## Config pairing

- Pretraining configs contain mask settings: `DATA.MASK_PATCH_SIZE`, `DATA.MASK_RATIO`, and model encoder settings.
- Fine-tuning configs use the classification head and may change image/window size.
- When image/window sizes change, checkpoint remapping can interpolate relative position bias tables.

## Safe validation

Use the validator to check command shape and the smoke script to test synthetic mask/loss behavior. Neither runs distributed training or downloads checkpoints.
