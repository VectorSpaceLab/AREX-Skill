# Evaluation Workflows

## When To Read

Read this for metric computation, `full_eval.py`, paper-style benchmark runs, and decisions about expensive or network-heavy evaluation tasks.

## Metrics Flow

After `render.py` has written test renders and GT images, run:

```bash
python metrics.py -m <model-a> <model-b> ...
```

For each model path, metrics are computed for every method directory under `<model>/test/`. The script writes:

- `<model>/results.json`: mean SSIM, PSNR, and LPIPS per method.
- `<model>/per_view.json`: per-image SSIM, PSNR, and LPIPS.

Metrics implementation notes:

- SSIM comes from the repo's loss utility.
- PSNR comes from the repo's image utility.
- LPIPS uses the bundled `lpipsPyTorch` implementation with VGG in `metrics.py`.
- The script sets CUDA device 0 and moves tensors to CUDA.

## Full Evaluation Orchestration

`full_eval.py` automates training, rendering, and metrics over MipNeRF360, Tanks&Temples, and Deep Blending scene lists.

Baseline shape:

```bash
python full_eval.py -m360 <mipnerf360-folder> -tat <tanks-and-temples-folder> -db <deep-blending-folder>
```

Useful flags:

- `--skip_training`
- `--skip_rendering`
- `--skip_metrics`
- `--output_path <dir>`
- `--use_depth`
- `--use_expcomp`
- `--fast` for sparse Adam / accelerated rasterizer experiments
- `--aa` for antialiasing

The README reports about seven hours on an A6000 for the full process. Treat this as an expensive benchmark run, not a smoke test.

## Evaluating Pretrained or Paper Images

If pretrained models are downloaded separately, use `--skip_training` and set `--output_path` to the pretrained model directory, while still providing source datasets for rendering.

If evaluation images have already been rendered/downloaded and no rendering is needed, use `--skip_training --skip_rendering` and point metrics at the image/model directories.

## Safe Verification Policy

- Parser/help checks are safe.
- Output-layout validators are safe.
- Full benchmark training/rendering/metrics is not safe by default because it needs large datasets, CUDA time, and possibly downloads.
- LPIPS may require torchvision model weights/cache when a fresh environment does not already have them. Do not silently trigger network downloads in verification.

## Results Interpretation

`results.md` documents comparisons for:

- default rasterizer with depth regularization and antialiasing,
- accelerated rasterizer with default optimizer,
- accelerated rasterizer with Sparse Adam,
- exposure compensation,
- training-time comparisons.

Use those results as qualitative guidance for feature selection, not as guaranteed metrics for a different dataset/environment.
