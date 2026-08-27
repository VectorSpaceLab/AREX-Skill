# Configuration

## Required package stack

Use the pinned OpenMMLab stack from the MambaVision segmentation README:

```bash
python -m pip install \
  mmengine==0.10.1 \
  mmcv==2.1.0 \
  opencv-python-headless \
  mmsegmentation==1.2.2 \
  mmdet==3.3.0 \
  mmpretrain==1.2.0
```

A CUDA-enabled PyTorch wheel is still required; rebuild or reinstall `mmcv` if the active torch/CUDA combination changes.

## Config map

All four segmentation configs use `backbone.type='MM_mamba_vision'`, `out_indices=(0, 1, 2, 3)`, and a UPerNet decoder with `num_classes=150`.

| Config id | File | Crop | Backbone settings | Decoder channels | Pretrained checkpoint | Optimizer wrapper | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tiny | `<mambavision-segmentation-config-root>/mamba_vision_160k_ade20k-512x512_tiny.py` | 512x512 | `dim=80`; `in_dim=32`; `depths=(1, 3, 8, 4)`; `num_heads=(2, 4, 8, 16)`; `window_size=(8, 8, 64, 32)`; `drop_path_rate=0.3`; `layer_scale=None` | `[80, 160, 320, 640]`, aux `320` | `mambavision_tiny_1k.pth.tar` | `AmpOptimWrapper` + AdamW `lr=5e-5`, `weight_decay=0.01` | published paper batch: 16 GPUs, 2 nodes, 1 image/GPU |
| small | `<mambavision-segmentation-config-root>/mamba_vision_160k_ade20k-512x512_small.py` | 512x512 | `dim=96`; `in_dim=64`; `depths=(3, 3, 7, 5)`; `num_heads=(2, 4, 8, 16)`; `window_size=(8, 8, 160, 56)`; `drop_path_rate=0.7`; `layer_scale=None` | `[96, 192, 384, 768]`, aux `384` | `mambavision_small_1k.pth.tar` | `AmpOptimWrapper` + AdamW `lr=6e-5`, `weight_decay=0.01` | published paper batch: 8 GPUs, 1 node, 2 images/GPU |
| base | `<mambavision-segmentation-config-root>/mamba_vision_160k_ade20k-512x512_base.py` | 512x512 | `dim=128`; `in_dim=64`; `depths=(3, 3, 10, 5)`; `num_heads=(2, 4, 8, 16)`; `window_size=(8, 8, 64, 32)`; `drop_path_rate=0.4`; `layer_scale=1e-5` | `[128, 256, 512, 1024]`, aux `512` | `mambavision_base_1k.pth.tar` | `AmpOptimWrapper` + AdamW `lr=5e-5`, `weight_decay=0.01` | published paper batch: 16 GPUs, 2 nodes, 1 image/GPU |
| L3 | `<mambavision-segmentation-config-root>/mamba_vision_160k_ade20k-640x640_l3_21k.py` | 640x640 | `dim=256`; `in_dim=64`; `depths=(3, 3, 20, 10)`; `num_heads=(4, 8, 16, 32)`; `window_size=(8, 8, 64, 32)`; `drop_path_rate=0.8`; `layer_scale=1e-5` | `[256, 512, 1024, 2048]`, aux `1024` | `mambavision_L3_21k_700m_512.pth.tar` | `OptimWrapper` + AdamW `lr=8e-5`, `weight_decay=0.05` | do not force AMP; config already avoids `AmpOptimWrapper` |

## Why the optimizer differs

- Tiny, small, and base use `AmpOptimWrapper` because their published recipes expect mixed precision.
- L3 intentionally uses `OptimWrapper` because the source config warns that AMP can be unstable for the 700M L3 checkpoint.
- If you override the optimizer wrapper, keep the learning rate and weight decay consistent with the chosen family unless you are deliberately re-tuning.

## ADE20K layout

Use the raw ADE20K release tree with the standard labels and `reduce_zero_label=True` handling from the config:

```text
ADEChallengeData2016/
  images/
    training/
    validation/
  annotations/
    training/
    validation/
```

The source dataset recipe expects the same relative subpaths for train, val, and test; only `data_root` changes.

A custom root can be injected with `--cfg-options` on all three dataloaders:

```bash
--cfg-options \
  train_dataloader.dataset.data_root=/datasets/ade20k/ADEChallengeData2016 \
  val_dataloader.dataset.data_root=/datasets/ade20k/ADEChallengeData2016 \
  test_dataloader.dataset.data_root=/datasets/ade20k/ADEChallengeData2016
```

## Published ADE20K results

| Backbone | Method | Lr Schd | mIoU | #Params(M) | FLOPs(G) | Resolution |
| --- | --- | --- | ---: | ---: | ---: | --- |
| MambaVision-T-1K | UPerNet | 160K | 46.0 | 55 | 945 | 512x512 |
| MambaVision-S-1K | UPerNet | 160K | 48.2 | 84 | 1135 | 512x512 |
| MambaVision-B-1K | UPerNet | 160K | 49.1 | 126 | 1342 | 512x512 |
| MambaVision-L3-512-21K | UPerNet | 160K | 53.2 | 780 | 3670 | 640x640 |

## Practical notes

- The 512x512 configs all use the same 160K schedule and 150 ADE20K classes.
- `<openmmlab-test-entrypoint>` reports `aAcc`, `mIoU`, and `mAcc`; `mIoU` is the metric to compare against the table above.
- If you change `dim` or `in_dim`, update `decode_head.in_channels` and `auxiliary_head.in_channels` so they match the four stage outputs.
