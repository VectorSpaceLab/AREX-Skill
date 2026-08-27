# Evaluation troubleshooting

## Missing dataset or checkpoint

Symptoms:

- `FileNotFoundError` for `tri_testlist.txt`, `train_log/flownet.pkl`, `RIFE_m_train_log/flownet.pkl`, or an HD YUV file.
- `NotADirectoryError` / `No such file or directory` for dataset roots.
- `AttributeError: 'NoneType' object has no attribute 'transpose'` after `cv2.imread(...)`, meaning an expected image file is missing or unreadable.

Fixes:

1. Run `python scripts/check_benchmark_layout.py --repo-root <checkout> --benchmark <name>` from this sub-skill directory, or use the script path directly.
2. Provide the external dataset at the exact repo-relative layout expected by the benchmark source.
3. Provide the external RIFE checkpoint as `train_log/flownet.pkl` for RIFE benchmarks or `RIFE_m_train_log/flownet.pkl` for HD 4X/RIFE_m.
4. Do not mark a data-backed benchmark as failed merely because assets are absent; classify it as `SKIP_DATA` unless the user explicitly supplied those assets.

## Checkpoint load errors

Symptoms:

- `FileNotFoundError: .../flownet.pkl`.
- `RuntimeError` from `load_state_dict` about missing/unexpected keys.
- GPU/CPU deserialization issues from `torch.load`.

Likely causes:

- The checkpoint directory exists but does not contain `flownet.pkl`.
- The file is not the RIFE/RIFE_m evaluation checkpoint expected by these scripts.
- The checkpoint state dict format differs from what `Model.load_model` expects.

Fixes:

- Confirm the right checkpoint family: RIFE uses `train_log`; RIFE_m HD 4X uses `RIFE_m_train_log` and `Model(arbitrary=True)`.
- Keep official metric claims disabled until a matching checkpoint, dataset, and backend have actually been run.
- If using a nonstandard checkpoint, first perform a small controlled inference workflow through the interpolation/root smoke path before attempting a full benchmark.

## CUDA-only HD failures

Symptoms:

- `AssertionError: Torch not compiled with CUDA enabled`.
- `RuntimeError: Found no NVIDIA driver` or `CUDA error`.
- CPU smoke checks pass, but `benchmark/HD.py` or `benchmark/HD_multi_4X.py` fails immediately.

Cause:

- The HD scripts explicitly call `.cuda()` on input tensors. Their earlier `device = torch.device(...)` line does not provide a CPU fallback for those tensors.

Fixes:

- Treat HD and HD 4X as `required-CUDA`; do not run them as CPU verification.
- If CUDA is unavailable, report `required-CUDA` rather than a model-quality failure.
- If CUDA is available but memory is tight, reduce verification scope or mark `SKIP_EXPENSIVE`; the source scripts process large 544p/720p/1080p YUV frames.

## `scikit-image`, PIL, and YUV reader issues

Symptoms:

- `ModuleNotFoundError: No module named 'skimage'`.
- `ModuleNotFoundError` or image conversion errors from `PIL`.
- HD PSNR becomes `nan` or the loop breaks early.

Causes:

- HD benchmarks require `skimage.color.rgb2yuv`/`yuv2rgb` through `yuv_frame_io.py`; this dependency is not listed in `requirements.txt`.
- HD files are expected to be YUV420 with the exact hard-coded width/height pairs.
- Short or corrupted YUV files may not contain frames `0..100` needed by the full source loops.

Fixes:

- Install `scikit-image` in the runtime environment before HD evaluation.
- Use `scripts/check_benchmark_layout.py --benchmark hd --strict` to check expected filenames and minimum frame sizes.
- Verify that files are raw YUV420, not wrapped videos renamed with `.yuv`.

## Shape, padding, and image layout errors

Symptoms:

- Tensor shape mismatch in `model.inference`.
- Cropped output and ground truth have incompatible shapes.
- Unexpected low PSNR/SSIM after a seemingly successful run.

Script-specific details:

- MiddleBury pads inputs into a `480x640` canvas and crops predictions back to source height/width.
- ATD12K pads two rows at top and bottom, then crops `[:, 2:-2]` from the prediction.
- HD uses vertical padding by resolution: 24 pixels for 720p, 4 for 1080p, and 16 for 544p.
- OpenCV loads images as BGR; the source scripts keep this convention consistently for both prediction and ground truth.

Fixes:

- Validate that every sampled dataset entry has the exact filenames documented in `benchmarks.md`.
- Avoid substituting arbitrary image layouts for official benchmarks unless the goal is a custom smoke, not official metrics.
- For custom subsets, report them as subset or smoke metrics, not README-equivalent results.

## Metric interpretation traps

- PSNR: higher is better; sensitive to exact image scaling and rounding.
- SSIM: higher is better; these scripts use `model.pytorch_msssim.ssim_matlab` and rounded predictions.
- MiddleBury IE: lower is better; the script prints the running mean of absolute pixel error.
- HD PSNR: computed on the Y channel after RGB-to-YUV conversion.
- `benchmark/testtime.py`: timing only. It does not load a checkpoint and cannot validate quality.

Do not compare numbers across datasets, checkpoints, or custom subsets as if they were the same official benchmark.

## Slow or expensive runs

- `benchmark/testtime.py` performs 100 warmup and 100 timed inferences at `480x640`; it is data-free but can still be expensive on CPU.
- Full UCF101/Vimeo90K/ATD12K sweeps can be long on CPU or when the dataset is large.
- HD benchmarks process large YUV files and require CUDA.

Use these decisions:

- `safe smoke candidate`: `benchmark/testtime.py` when dependencies and runtime budget are available.
- `SKIP_DATA`: missing datasets/checkpoints or any required network download.
- `SKIP_EXPENSIVE`: assets exist but full benchmark exceeds approved budget.
- `required-CUDA`: HD scripts when CUDA is not available.
