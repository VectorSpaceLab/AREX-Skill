# Alignment and Data Preparation

## SHHQ access

The StyleGAN-Human documentation describes SHHQ as non-commercial research data with an agreement and institutional request process. Do not assume the dataset is freely downloadable. Keep any released dataset and signed agreement outside the skill directory.

## Background whitening

Input layout is a raw-image directory and a segmentation-mask directory with matching filenames. The bundled helper performs a blurred foreground/background composite and writes the result to a separate output directory:

```bash
python sub-skills/stylegan-human-manipulation/scripts/bg_white.py \
  --raw-img-dir SHHQ-1.0/no_segment \
  --raw-seg-dir SHHQ-1.0/segments \
  --outdir SHHQ-1.0/bg_white
```

Check that raw and mask images have compatible dimensions and that masks are readable by OpenCV. This is the only selected human-manipulation utility that is CPU-safe and model-free.

## Raw-photo alignment

The source alignment workflow expects:

- An image folder containing one-person images.
- An OpenPose body model at the expected model path.
- PP-HumanSeg exported and pretrained model directories.
- Paddle/PaddleSeg-compatible runtime and CUDA.
- Output folder for aligned 512x1024 images.

The algorithm segments the person, extracts the largest contour, detects body keypoints, rejects images with multiple/low-confidence people, pads/crops to a 1:2 human-image shape, and writes a resized result. Use the preflight helper first. If a photo contains multiple people or a partial body, expect it to be skipped rather than forced through.

## Data validation checklist

1. Every input image is readable and has one intended person.
2. Segmentation model config and weights are in the exact expected directories.
3. Output directory is writable and empty or versioned for the current run.
4. CUDA and OpenCV/Paddle dependencies are available.
5. The resulting aligned image is visually inspected before PTI.

Alignment is an asset-gated workflow; a Python import or image-shape check is not equivalent to a successful segmentation/keypoint run.
