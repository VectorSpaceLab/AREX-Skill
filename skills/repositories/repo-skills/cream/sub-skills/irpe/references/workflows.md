# iRPE Workflows

## DeiT with iRPE

### Build the config snippet

Use the bundled config builder to print the RPE snippet for a DeiT model:

```bash
python ../scripts/build_irpe_config.py --ratio 1.9 --method product --mode ctx --shared-head --skip 0 --rpe-on k
```

### Train or evaluate

```bash
python -m torch.distributed.launch --nproc_per_node=8 --use_env main.py \
  --model deit_tiny_patch16_224_ctx_product_50_shared_k --data-path <imagenet-root> \
  --eval --resume <checkpoint>
```

## DETR with iRPE

### Train or evaluate

```bash
python -m torch.distributed.launch --nproc_per_node=8 main.py \
  --enc_rpe2d <rpe-choice> --coco_path <coco-root> --output_dir <output-dir>
```

## Integration steps

1. Choose the target branch: DeiT or DETR.
2. Build the RPE config snippet with the bundled helper.
3. Confirm whether the optional compiled `rpe_ops` extension is available.
4. Use the launcher template that matches the model family.

## Input assumptions

- DeiT workflows use ImageNet-1k.
- DETR workflows use COCO 2017.
- Non-square and variable-resolution inputs are supported by the iRPE design.
