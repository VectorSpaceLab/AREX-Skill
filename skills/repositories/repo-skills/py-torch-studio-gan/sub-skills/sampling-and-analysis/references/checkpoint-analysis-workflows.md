# Checkpoint Analysis Workflows

## Purpose

Read this when a user wants to use an existing StudioGAN checkpoint for generated-image saving, real/fake image folders, visual canvases, KNN memorization checks, interpolation, frequency analysis, t-SNE, intra-class FID, CAS, SeFa, truncation, or Langevin/DDLS-aware sampling.

This reference is distilled from StudioGAN's public `src/main.py` CLI, checkpoint-loading flow, worker analysis methods, sampling utilities, and README analysis examples. It is self-contained: use it with a separate StudioGAN checkout and do not rely on any earlier source checkout used to create the skill.

## Baseline command shape

The checkpoint-analysis entry point is `src/main.py` in a StudioGAN checkout:

```bash
CUDA_VISIBLE_DEVICES=0 python /path/to/PyTorch-StudioGAN/src/main.py \
  -cfg /path/to/config.yaml \
  -ckpt /path/to/checkpoint-directory \
  -save /path/to/analysis-output \
  -data /path/to/data \
  -metrics none \
  <analysis flags>
```

Prefer building the command with [../scripts/build_checkpoint_analysis_command.py](../scripts/build_checkpoint_analysis_command.py) because it checks the most common incompatibilities and prints a command without executing it.

## Pre-run checklist

- Match the checkpoint to its YAML config family. A BigGAN/ContraGAN checkpoint cannot be analyzed safely with a StyleGAN config, and class-conditional analyses need the matching class-conditioned config.
- Use a checkpoint directory, not an individual `.pth` file. StudioGAN expects files named like `model=G-best-weights-step=*.pth`, `model=D-best-weights-step=*.pth`, and usually current G/D companions. Final analysis reloads the best checkpoint after initial checkpoint loading.
- Use `-metrics none` unless the user intentionally wants checkpoint metric evaluation before the visual/sampling analyses. Standalone image-folder metrics belong in [evaluation-metrics](../../evaluation-metrics/SKILL.md).
- Provide `-data` for real/reference workflows: save-real, KNN, frequency, t-SNE, iFID, and CAS. For CIFAR datasets, StudioGAN may try to prepare/download supported data if the directory is supplied; for custom data, the directory must already follow the expected dataset layout.
- Keep `-DDP` off. Use a single visible GPU (`CUDA_VISIBLE_DEVICES=0`) or DataParallel by exposing multiple GPUs without `-DDP`.
- Check `OPTIMIZATION.batch_size` in the config. Visualization, KNN, interpolation, iFID, and CAS require the batch size to be divisible by 8.
- Choose a fresh or disposable `-save` directory when saving image folders, because StudioGAN recreates `samples/<run_name>/real` or `samples/<run_name>/fake` subdirectories for image export.

## Analysis execution order

After model construction and checkpoint loading, StudioGAN switches to analysis mode, reloads the best checkpoint, and then runs selected work in this order:

1. Optional checkpoint metrics if `-metrics` is not `none`.
2. `-sr` save real images.
3. `-sf` save fake images.
4. `-v` generated-image canvas.
5. `-knn` K-nearest-neighbor memorization analysis.
6. `-itp` linear interpolation, first fixed latent `z`, then fixed class embedding `y`.
7. `-fa` frequency analysis.
8. `-tsne` discriminator-embedding t-SNE.
9. `-ifid` intra-class FID.
10. `-sefa` semantic factorization.
11. `--GAN_train` CAS recall mode.
12. `--GAN_test` CAS precision mode.

When combining flags, expect outputs and runtime costs in that order. If one earlier analysis fails, later analyses do not run.

## Workflows

### Save generated images

Use this when the user needs class-organized fake PNGs from the generator.

Builder example:

```bash
python scripts/build_checkpoint_analysis_command.py \
  --repo-root /path/to/PyTorch-StudioGAN \
  --cfg /path/to/config.yaml \
  --checkpoint /path/to/checkpoint-directory \
  --save-dir /path/to/analysis-output \
  --gpus 0 \
  --save-fake --fake-count 1000
```

Native flags: `-sf -sf_num 1000`.

Output: `samples/<run_name>/fake/<class>/<index>.png` under the save directory. Generation uses the configured latent prior, class sampling, truncation if requested, and the best checkpoint.

Interpretation: use these images for qualitative review or as inputs to separate image-folder metric commands. This is the least dataset-dependent checkpoint workflow.

### Save reference images

Use this when the user wants a class-organized real-image folder matching the dataset/reference selection.

Builder action: `--save-real` with `--data-dir`.

Native flag: `-sr`.

Output: `samples/<run_name>/real/<class>/<index>.png`.

Interpretation: the folder contains samples from the selected reference dataset, not generated images. It is useful for visual audits or for later image-folder metrics.

### Visualize generated canvases

Use this when the user wants a quick generated-image canvas from the checkpoint.

Builder action: `--visualize`.

Native flag: `-v`.

Output: `figures/<run_name>/generated_canvas_<best_step>.png`.

Interpretation: for class-conditional models, StudioGAN chooses class labels in an ordered/canvas-friendly way when possible. If the current config raises a `data_dir` assertion even though the workflow mostly samples from the checkpoint, rerun with `--data-dir /path/to/data`.

### KNN memorization check

Use this when the user asks whether generated images are near training/reference examples.

Builder action: `--knn` with `--data-dir`.

Native flag: `-knn`.

Output: `figures/<run_name>/fake_anchor_<num_cols>NN_<class_count>_classes.png`. The first column is generated; the remaining columns are nearest real images. StudioGAN uses a fixed 8-column canvas, so it effectively shows 7 nearest neighbors per generated anchor.

Interpretation:

- Similar nearest neighbors may indicate memorization, dataset duplicates, or class-level similarity; inspect visually before making a strong claim.
- The workflow uses a ResNet50 feature extractor through a hub/backbone path and may require cached or downloadable weights.
- It loops over classes and can be slow on large class counts.

### Linear interpolation

Use this when the user asks for latent-space smoothness or class-conditioning interpolation.

Builder action: `--interpolation`.

Native flag: `-itp`.

Output: `figures/<run_name>/<index>_Interpolated_images_fix_z.png` and `figures/<run_name>/<index>_Interpolated_images_fix_y.png`; StudioGAN saves many grids by default.

Compatibility:

- Supported only for `big_resnet`, `big_resnet_deep_legacy`, and `big_resnet_deep_studiogan` backbones.
- Do not use it for StyleGAN2/StyleGAN3 checkpoints; StudioGAN rejects that combination.

Interpretation: fixed-`z` grids vary class embedding at a stable latent sample; fixed-`y` grids vary latent vectors for a stable class embedding.

### Frequency analysis

Use this when the user asks about spectral artifacts or real/fake frequency statistics.

Builder action: `--frequency` with `--data-dir`.

Native flag: `-fa`.

Output: `figures/<run_name>/dfft_spectrum.png`.

Interpretation: the plot compares average shifted Fourier spectra of real and fake images. It is qualitative; use it to spot obvious high-frequency or low-frequency artifacts, not as a full metric replacement.

### t-SNE discriminator embedding plot

Use this when the user wants real/fake embedding separability in discriminator feature space.

Builder action: `--tsne` with `--data-dir`.

Native flag: `-tsne`.

Output: `figures/<run_name>/tsne_scatter_real.png` and `figures/<run_name>/tsne_scatter_fake.png`.

Interpretation:

- StudioGAN hooks the discriminator layer named `linear1` and runs t-SNE with 2 components, perplexity 40, and 300 iterations.
- If the dataset has more than 10 classes, it randomly selects 10 classes for the scatter plot.
- Compare structure and class separation qualitatively; t-SNE axes are not directly comparable across separate runs.

### Intra-class FID

Use this when the user asks for per-class fidelity/diversity rather than one global FID.

Builder action: `--ifid` with `--data-dir`.

Native flag: `-ifid`.

Output: `statistics/<run_name>/iFID.npy` and log entries, including an average iFID.

Interpretation: StudioGAN computes real moments and fake features per class, then records per-class FID values. Metric backbones may require cached/downloadable weights and the workflow can be expensive for many classes.

### CAS recall and precision

Use this when the user asks for Classifier Accuracy Score:

- `--gan-train` / native `--GAN_train`: CAS recall mode.
- `--gan-test` / native `--GAN_test`: CAS precision mode.
- `--resume-classifier-train` / native `-resume_ct`: resume a previously saved CAS classifier if present.

Requirements:

- A class-conditioned discriminator config; unconditioned (`d_cond_mtd: W/O`) configs are invalid for CAS.
- Dataset/reference data.
- Long runtime budget. StudioGAN trains a classifier, commonly much longer than image visualization.

Outputs: CAS classifier checkpoint files in the checkpoint directory, plus top-1/top-5 log lines.

Interpretation: treat CAS as a class-conditional precision/recall proxy; confirm which mode was used before comparing results.

### SeFa semantic factorization

Use this when the user asks for semantic axis traversals on a BigGAN-style generator.

Builder example:

```bash
python scripts/build_checkpoint_analysis_command.py \
  --repo-root /path/to/PyTorch-StudioGAN \
  --cfg /path/to/biggan-config.yaml \
  --checkpoint /path/to/checkpoint-directory \
  --save-dir /path/to/analysis-output \
  --gpus 0 \
  --sefa --sefa-axis 5 --sefa-max 2.0
```

Native flags: `-sefa -sefa_axis 5 -sefa_max 2.0`.

Output: `figures/<run_name>/<index>_sefa_images.png`.

Compatibility:

- `-sefa_axis` must be positive.
- SeFa is BigGAN-focused in StudioGAN and relies on generator weights used for closed-form factorization.
- Do not use SeFa for StyleGAN2/StyleGAN3 in StudioGAN; config compatibility rejects it.

Interpretation: each row traverses a semantic axis. Increasing `-sefa_max` makes stronger variations but can move away from realistic images.

### Truncation and sampling statistics

Truncation modifies sampling for the selected analysis actions:

- Non-StyleGAN generators: `--truncation_factor` accepts `-1` for no truncation or a non-negative threshold for truncated normal sampling.
- StyleGAN2/StyleGAN3: `--truncation_factor` must be between `0` and `1`; `--truncation_cutoff` limits which W-space layers receive truncation.

BatchNorm statistics controls:

- `-std_stat -std_max <N> -std_step <S>` accumulates standing statistics before evaluation/analysis.
- `-batch_stat` uses the current batch statistics during evaluation.
- Do not combine standing statistics and batch statistics.

### Langevin/DDLS-aware sampling

Use this only when the user explicitly asks for DDLS or Langevin sampling during analysis.

Builder example:

```bash
python scripts/build_checkpoint_analysis_command.py \
  --repo-root /path/to/PyTorch-StudioGAN \
  --cfg /path/to/config.yaml \
  --checkpoint /path/to/checkpoint-directory \
  --save-dir /path/to/analysis-output \
  --data-dir /path/to/data \
  --gpus 0 \
  --knn --langevin --lgv-rate 0.1 --lgv-std 0.01 --lgv-steps 10
```

Native flags: `-lgv -lgv_rate ... -lgv_std ... -lgv_steps ...`, optionally `-lgv_decay -lgv_decay_steps`.

Requirements:

- Must accompany at least one analysis action.
- Requires a Gaussian latent prior.
- Cannot be combined with latent optimization (`LOSS.apply_lo`).
- Cannot be used with DDP.
- Requires gradients during sampling, so it is slower and more memory-intensive than ordinary image generation.

## Output directory map

StudioGAN writes under the `-save` root:

| Output root | What appears there |
| --- | --- |
| `samples/<run_name>/real/<class>/*.png` | Real/reference image export from `-sr` |
| `samples/<run_name>/fake/<class>/*.png` | Fake image export from `-sf` |
| `figures/<run_name>/*.png` | Visualization canvas, KNN grids, interpolation grids, frequency plot, t-SNE plots, SeFa grids |
| `statistics/<run_name>/iFID.npy` | Intra-class FID values |
| `logs/<run_name>.log` | Analysis logs and metric/CAS summaries |

`<run_name>` usually comes from the checkpoint's saved run metadata when loading an existing checkpoint.
