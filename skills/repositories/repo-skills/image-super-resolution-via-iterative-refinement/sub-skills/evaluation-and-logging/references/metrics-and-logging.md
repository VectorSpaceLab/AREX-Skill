# Metrics and logging behavior

## Result-pair evaluation

The repository evaluates super-resolution quality by pairing a generated final SR image with its matching ground-truth HR image:

- HR filename suffix: `*_hr.png`
- final SR filename suffix: `*_sr.png`
- pair key: the filename stem before the suffix, for example `12000_3_hr.png` pairs with `12000_3_sr.png`

Use the bundled helper when you need a clear, standalone check:

```bash
python skills/disco/image-super-resolution-via-iterative-refinement/sub-skills/evaluation-and-logging/scripts/evaluate_result_pairs.py results
```

Common options:

```bash
# show every per-pair metric as well as the summary
python skills/disco/image-super-resolution-via-iterative-refinement/sub-skills/evaluation-and-logging/scripts/evaluate_result_pairs.py results --per-image

# evaluate separate directories while still pairing by stem
python skills/disco/image-super-resolution-via-iterative-refinement/sub-skills/evaluation-and-logging/scripts/evaluate_result_pairs.py --hr-dir hr_outputs --sr-dir sr_outputs

# inspect nested result directories
python skills/disco/image-super-resolution-via-iterative-refinement/sub-skills/evaluation-and-logging/scripts/evaluate_result_pairs.py results --recursive
```

The helper exits non-zero with explicit messages when no HR/SR files are found, when pair stems do not match, or when image shapes are incompatible. This is safer than relying on sorted filename zipping.

## Metric semantics

Implemented metric assumptions match the repository's evaluation intent:

- Images are converted to RGB arrays in `[0, 255]` before scoring.
- PSNR is `20 * log10(255 / sqrt(MSE))` over all pixels and channels.
- PSNR is reported as `inf` for exactly identical images.
- SSIM uses constants `C1=(0.01*255)^2`, `C2=(0.03*255)^2`, and an 11×11 Gaussian window with sigma 1.5.
- No border shave, luma-only conversion, face crop, or dataset-specific masking is applied.
- SSIM requires image height and width of at least 11 pixels because of the Gaussian window.

Treat scores as comparable only when the same output resolution, dataset split, preprocessing, reverse diffusion step budget, and metric implementation are used. The README result table reports PSNR/SSIM for the provided FFHQ-CelebaHQ tasks, but those numbers are not a built-in acceptance threshold for arbitrary user data.

## Output file contracts

`sr.py` and `infer.py` produce the HR/SR filename pairs consumed by result-pair evaluation. `sample.py` is unconditional generation and does not produce ground-truth HR pairs for PSNR/SSIM.

| Script and mode | Relevant output names | Evaluation notes |
| --- | --- | --- |
| `sr.py -p train` validation checkpoints | `results/<epoch>/<step>_<idx>_hr.png`, `..._sr.png`, `..._lr.png`, `..._inf.png` | Computes validation PSNR only during training; use the bundled helper on an epoch subdirectory for PSNR+SSIM after the run. |
| `sr.py -p val` | `results/<step>_<idx>_sr_process.png`, `..._sr.png`, `..._hr.png`, `..._lr.png`, `..._inf.png` | Computes PSNR and SSIM for the final `..._sr.png` image against `..._hr.png`. Ignore `..._sr_process.png` for quantitative scoring. |
| `infer.py -p val` | `results/<step>_<idx>_sr_process.png`, `..._sr.png`, `..._hr.png`, `..._inf.png` | Writes the same final SR/HR pair pattern; W&B inference tables do not include PSNR/SSIM unless scored separately. |
| `sample.py -p train` validation | `results/<epoch>/<step>_<idx>_sr.png` | These are unconditional samples, not SR/HR pairs. Do not run pair metrics unless separate HR matches are supplied. |
| `sample.py -p val` | `results/<step>_<idx>_sample_process.png`, `..._sample.png` | No ground-truth HR output. Use visual or distributional evaluation outside this sub-skill. |

Repository config paths named `results`, `log`, `tb_logger`, and `checkpoint` are expanded under a timestamped experiment directory by the logger parser. If a run created a timestamped experiment folder, evaluate the concrete result subdirectory that contains image files rather than the literal config value.

## TensorBoard and W&B logging

### TensorBoard

The training and inference entrypoints construct a TensorBoard writer with `opt['path']['tb_logger']`.

- `sr.py -p train` logs training loss scalars at `print_freq`, validation image panels named `Iter_<step>`, and a scalar named `psnr` after validation.
- `sample.py -p train` logs training loss scalars and sample image panels named `Iter_<step>`.
- `sr.py -p val`, `infer.py`, and `sample.py -p val` create the writer but do not add the same scalar/image stream as the train-time validation loop.

### Weights & Biases

Enable W&B with `-enable_wandb`. The run uses the `wandb.project` value from the selected JSON config and stores W&B run files below the experiments area.

Supported flags and behavior:

- `sr.py -enable_wandb`: logs train losses and validation preview images; defines validation step metrics.
- `sr.py -enable_wandb -log_wandb_ckpt`: logs generator and optimizer checkpoint files as a W&B model artifact at checkpoint save time.
- `sr.py -p val -enable_wandb -log_eval`: builds an `eval_data` table with fake/interpolated image, final SR image, HR image, PSNR, and SSIM; also logs summary `PSNR` and `SSIM` metrics.
- `infer.py -enable_wandb -log_infer`: builds an `infer_data` table with fake/interpolated image, final SR image, and HR image.
- `sample.py -enable_wandb`: logs validation/sample images; it has no `-log_eval` or `-log_infer` table flag.

W&B must be installed and authenticated before use. If a task does not require online experiment tracking, omit `-enable_wandb` to avoid import, login, and network dependencies.
