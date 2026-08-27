# Salient Object and Human Segmentation Workflows

Use the bundled helper `../scripts/u2net_infer.py` for self-contained U-2-Net image-folder inference. It embeds the U-2-Net model code needed for inference and does not depend on the original source checkout.

## What the official scripts do

The generic saliency and human segmentation scripts follow the same pipeline:

1. Read every image file from an input directory.
2. Resize to a square preprocessing size of 320.
3. Normalize RGB channels with ImageNet-style means/stds.
4. Instantiate `U2NET(3,1)` or `U2NETP(3,1)`.
5. Load a `.pth` state dict.
6. Run `net.eval()` and take the first fused output, channel 0.
7. Normalize the probability map with `(pred - pred.min()) / (pred.max() - pred.min())`.
8. Save an RGB PNG mask using the input filename stem, resized back to the original image dimensions.

The helper preserves these behaviors while adding explicit CLI arguments, safe CPU `map_location`, sorted input processing, JSON summaries, bounded `--max-images`, and clearer missing-weight errors.

## Generic saliency with `u2netp` on CPU

```bash
python scripts/u2net_infer.py \
  --task saliency \
  --model u2netp \
  --weights PATH_TO_WEIGHTS/u2netp.pth \
  --input-dir INPUT_IMAGES \
  --output-dir OUTPUT_MASKS \
  --device cpu
```

Expected behavior:

- output directory is created if needed;
- each supported input image becomes one `.png` mask;
- output dimensions match the original image dimensions, not the 320 preprocessing size;
- the JSON summary lists processed images and saved paths.

## Generic saliency with full `u2net`

```bash
python scripts/u2net_infer.py \
  --task saliency \
  --model u2net \
  --weights PATH_TO_WEIGHTS/u2net.pth \
  --input-dir INPUT_IMAGES \
  --output-dir OUTPUT_MASKS \
  --device auto
```

`--device auto` uses CUDA only when PyTorch reports CUDA as available; otherwise it stays on CPU. The full model is much larger than `u2netp`, so CPU inference can be slow.

## Human segmentation

The human segmentation checkpoint uses full `U2NET(3,1)`:

```bash
python scripts/u2net_infer.py \
  --task human \
  --weights PATH_TO_WEIGHTS/u2net_human_seg.pth \
  --input-dir HUMAN_IMAGES \
  --output-dir HUMAN_MASKS \
  --device auto
```

The README notes that the human model is intended for general human/person segmentation and should not be expected to produce hair-level matting quality.

## Smoke-test plumbing without pretrained weights

```bash
python scripts/u2net_infer.py \
  --task saliency \
  --model u2netp \
  --input-dir INPUT_IMAGES \
  --output-dir SMOKE_MASKS \
  --device cpu \
  --max-images 1 \
  --allow-random-weights-for-smoke
```

Smoke mode intentionally uses random model weights when `--weights` is omitted. It is useful for assertion-backed plumbing checks, but the masks have no pretrained saliency or segmentation quality.

## CLI contract

Important options:

| Option | Meaning |
| --- | --- |
| `--task {saliency,human}` | Selects generic saliency or human/person segmentation behavior. |
| `--model {u2net,u2netp}` | Saliency architecture. Human mode always uses full `U2NET`. |
| `--weights PATH` | Explicit `.pth` state dict. Required unless random smoke mode is enabled. |
| `--input-dir DIR` | Directory of input images. The helper filters common image extensions. |
| `--output-dir DIR` | Destination directory for PNG masks. Created if missing. |
| `--resize INT` | Square preprocessing size. Default: `320`. |
| `--device {auto,cpu,cuda}` | Device selection. Explicit `cuda` fails clearly if unavailable. |
| `--max-images N` | Bound runtime for quick checks; images are processed in sorted order. |
| `--allow-random-weights-for-smoke` | Permit no-weight smoke checks. Never use for quality claims. |

## Output naming and validation

- Input `cat.photo.jpg` becomes output `cat.photo.png`.
- Masks are saved as RGB PNG images.
- Validate a run by checking `processed_count`, output file existence, and output image size against the corresponding source image.
