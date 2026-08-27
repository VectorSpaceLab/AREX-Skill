# Saliency and Human Segmentation Model Weights

## Purpose

Use this reference to choose the correct `.pth` file for the bundled inference helper. The generated skill does not bundle pretrained weights or download them automatically.

## Weight matrix

| Task | Helper options | Expected checkpoint | Architecture |
| --- | --- | --- | --- |
| Full salient object detection | `--task saliency --model u2net` | `u2net.pth` | `U2NET(3,1)` |
| Lightweight salient object detection | `--task saliency --model u2netp` | `u2netp.pth` | `U2NETP(3,1)` |
| Human/person segmentation | `--task human` | `u2net_human_seg.pth` | `U2NET(3,1)` |

The original README documents Google Drive and Baidu Pan locations for these weights. Treat downloads as a user-approved network step, not as a default action inside the skill.

## Placement

The bundled helper accepts any explicit path:

```bash
python scripts/u2net_infer.py \
  --task saliency \
  --model u2netp \
  --weights PATH_TO_WEIGHTS/u2netp.pth \
  --input-dir INPUT_IMAGES \
  --output-dir OUTPUT_MASKS
```

You do not need to recreate repository-specific checkpoint directories for the bundled helper; pass the checkpoint path directly with `--weights`.

## Troubleshooting selection mistakes

- Loading `u2net.pth` into `--model u2netp` usually produces missing/unexpected key or tensor-size errors.
- Loading `u2netp.pth` into full `U2NET` produces the inverse mismatch.
- Human segmentation uses the full `U2NET` architecture even though it is a specialized task.
- CPU execution should load weights with `map_location="cpu"`; the bundled helper does this automatically.

## No-weight smoke checks

`--allow-random-weights-for-smoke` is only for verifying dependencies, preprocessing, forward pass, and output writing. It must never be described as a pretrained inference result, a model-quality test, or a benchmark.
