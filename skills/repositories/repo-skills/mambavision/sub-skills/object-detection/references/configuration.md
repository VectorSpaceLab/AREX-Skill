# Configuration Reference

This reference distills the published MambaVision detection configs, result table, and data layout. Use it to pick the correct family and verify checkpoint compatibility before launching MMDetection.

## Required OpenMMLab stack

The README pins the following packages for the detection setup:

| Package | Version | Why it matters |
| --- | --- | --- |
| `mmengine` | `0.10.1` | runner, config, and registry surface |
| `mmcv` | `2.1.0` | ops and MMDetection compatibility |
| `opencv-python-headless` | recent 4.x build | image loading |
| `mmdet` | `3.3.0` | detector configs and CLI |
| `mmsegmentation` | `1.2.2` | shared registry imported by the adapter |
| `mmpretrain` | `1.2.0` | shared registry imported by the adapter |

The README also lists a validated runtime matrix of PyTorch `2.4.1+cu124`, CUDA `12.4`, and OpenCV `4.10.0`. Use a CUDA-capable PyTorch build that matches the `mmcv` wheel you install.

## Shared config contract

All three detection configs share the same MMDetection skeleton:

- detector: `Cascade Mask R-CNN`
- backbone type: `MM_mamba_vision`
- backbone outputs: `out_indices=(0, 1, 2, 3)`
- dataset: COCO instance segmentation
- heads: three cascade bbox heads with 80 classes
- training schedule: 36 epochs
- warmup and LR schedule: `LinearLR` warmup for 1000 iters, then `MultiStepLR` with milestones at epochs 27 and 33
- optimizer: `AmpOptimWrapper` with AdamW
- train pipeline: load image, load bbox+mask annotations, random flip, DETR/Sparse R-CNN style random choice resize/crop/resize, pack detection inputs

The backbone checkpoint path lives in `model.backbone.pretrained`. The detector checkpoint passed to `<openmmlab-test-entrypoint>` is separate and should point to a full MMDetection detector checkpoint, not the classification backbone file.

## Model family table

The published detection families are tiny, small, and base. The `small` and `base` configs inherit from the tiny config and override only the backbone/neck and optimizer settings.

| Family | Config file | Backbone checkpoint path | Depths | Num heads | Window size | Dim | In dim | Neck channels | Drop path | Layer scale | Train LR | box mAP | segm mAP | Params (M) | FLOPs (G) |
| --- | --- | --- | --- | --- | --- | ---: | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| Tiny | `<mambavision-detection-config-root>/cascade_mask_rcnn_mamba_vision_tiny_3x_coco.py` | `/ckpts/mambavision_tiny_1k.pth.tar` | `(1, 3, 8, 4)` | `(2, 4, 8, 16)` | `(8, 8, 112, 56)` | 80 | 32 | `[80, 160, 320, 640]` | `0.2` | `None` | `0.0001` | `51.1` | `44.3` | `86` | `740` |
| Small | `<mambavision-detection-config-root>/cascade_mask_rcnn_mamba_vision_small_3x_coco.py` | `/ckpts/mambavision_small_1k.pth.tar` | `(3, 3, 7, 5)` | `(2, 4, 8, 16)` | `(8, 8, 112, 56)` | 96 | 64 | `[96, 192, 384, 768]` | `0.3` | `None` | `0.0001` | `52.3` | `45.2` | `108` | `828` |
| Base | `<mambavision-detection-config-root>/cascade_mask_rcnn_mamba_vision_base_3x_coco.py` | `/ckpts/mambavision_base_1k.pth.tar` | `(3, 3, 10, 5)` | `(2, 4, 8, 16)` | `(8, 8, 112, 56)` | 128 | 64 | `[128, 256, 512, 1024]` | `0.5` | `1e-5` | `0.0002` | `52.8` | `45.7` | `145` | `964` |

The neck channels always follow `[dim, 2*dim, 4*dim, 8*dim]`.

## COCO layout expected by the config

The published data preparation expects COCO instance annotations at a root like `data/coco/`:

```text
data/coco/
├── annotations/
│   ├── instances_train2017.json
│   └── instances_val2017.json
├── train2017/
└── val2017/
```

The README also mentions `panoptic_train2017.json` as optional for panoptic experiments, but that file is not needed for the Cascade Mask R-CNN instance detection workflows here.

If the COCO root lives elsewhere, override `data_root` in `--cfg-options` rather than editing the shared config files.

## Path adaptation rules

- Use `model.backbone.pretrained` for the classification backbone checkpoint that initializes the detector backbone.
- Use the positional checkpoint argument to `<openmmlab-test-entrypoint>` for the full detector checkpoint you want to evaluate.
- Use `--cfg-options data_root=<path>` when the COCO root differs from the default `data/coco` layout.
- Keep the published family matched to the published checkpoint family; tiny/small/base are not interchangeable without shape and key mismatches.
