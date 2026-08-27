# Shared Configuration Behavior

## YACS config flow

`config.py` defines a global default `CfgNode` and merges YAML config files through `BASE` recursively. Command-line scripts call `get_config(args)`, which:

1. Loads `args.cfg` and any `BASE` configs.
2. Applies `args.opts` as flat `KEY VALUE` overrides.
3. Applies convenience flags such as `--batch-size`, `--data-path`, `--pretrained`, `--resume`, `--use-checkpoint`, and AMP/fused flags.
4. Sets `LOCAL_RANK` from `args.local_rank` on PyTorch 1.x or from the `LOCAL_RANK` environment variable on PyTorch 2.x.
5. Rewrites `OUTPUT` to `<output>/<MODEL.NAME>/<TAG>`.

## High-value config fields

- `DATA.DATASET`: `imagenet` or `imagenet22K` in this repo.
- `DATA.DATA_PATH`: root containing `train/` and `val/`, zipped ImageNet files, or ImageNet-22K JSON maps depending on workflow.
- `DATA.IMG_SIZE`, `MODEL.*.WINDOW_SIZE`, `MODEL.*.PATCH_SIZE`: must stay compatible for window partitioning and SimMIM masks.
- `MODEL.TYPE`: `swin`, `swinv2`, `swin_mlp`, or `swin_moe`.
- `MODEL.PRETRAINED`: fine-tune checkpoint loaded by `load_pretrained`.
- `MODEL.RESUME`: checkpoint used for resume/evaluation by `load_checkpoint`.
- `TRAIN.ACCUMULATION_STEPS` and `TRAIN.USE_CHECKPOINT`: first-line memory levers.
- `AMP_ENABLE` / `ENABLE_AMP`: supervised and SimMIM scripts use related but not identical field names.
- `FUSED_WINDOW_PROCESS`, `FUSED_LAYERNORM`, `TRAIN.OPTIMIZER.NAME`: optional backend acceleration surfaces.

## Override examples

```bash
--opts TRAIN.EPOCHS 100 TRAIN.WARMUP_EPOCHS 5
--opts DATA.IMG_SIZE 384 MODEL.SWIN.WINDOW_SIZE 12
--batch-size 64 --accumulation-steps 2 --use-checkpoint
```

Use list syntax carefully when overriding list fields from a shell, for example `MODEL.SWIN.DEPTHS [2,2,18,2]`. Validate complex overrides with `scripts/inspect_swin_config.py` before training.

## Launcher note

The original scripts document `python -m torch.distributed.launch`. Modern PyTorch workflows usually use `torchrun`. Both must populate distributed environment variables. Under PyTorch 2.x, set `LOCAL_RANK` through the launcher or the config loader raises an environment-key error before training starts.
