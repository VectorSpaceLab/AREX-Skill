# Analysis Flags Reference

## Purpose

Use this as the compact flag catalog for StudioGAN checkpoint sampling and post-training analysis through `src/main.py`. The bundled builder flag names are intentionally safer and longer; each maps to a native StudioGAN flag shown below.

The builder is [../scripts/build_checkpoint_analysis_command.py](../scripts/build_checkpoint_analysis_command.py). It prints a native command and does not execute it.

## Base arguments

| Builder flag | Native command part | Required? | Notes |
| --- | --- | --- | --- |
| `--repo-root /path/to/PyTorch-StudioGAN` | `python /path/to/PyTorch-StudioGAN/src/main.py` | Yes | Must point at a checkout containing `src/main.py`. |
| `--cfg CONFIG` | `-cfg CONFIG` | Yes | Use the YAML config matching the checkpoint family. Relative paths resolve under `--repo-root` in the builder output. |
| `--checkpoint CKPT_DIR` | `-ckpt CKPT_DIR` | Yes | Must be a checkpoint directory, not a single file. Best G/D files are needed for final analysis reload. |
| `--save-dir SAVE_DIR` | `-save SAVE_DIR` | Yes | StudioGAN writes `samples/`, `figures/`, `logs/`, and `statistics/` below this root. |
| `--data-dir DATA_DIR` | `-data DATA_DIR` | Required for data/reference workflows | Needed for save-real, KNN, frequency, t-SNE, iFID, and CAS. Also useful if config compatibility asks for data during visualization. |
| `--gpus 0` | `CUDA_VISIBLE_DEVICES=0` | Recommended | Use one GPU for the safest analysis path. Multiple visible GPUs use DataParallel when the config permits it; do not add DDP. |
| `--load-best` | `-best` | Optional | Requests best checkpoint during initial `-ckpt` loading. StudioGAN still reloads the best checkpoint before final analyses. |
| `--dry-run-no-path-check` | none | Optional | Lets the builder draft a command before paths exist; it still validates flag logic where possible. |

The builder always adds `-metrics none` so checkpoint metric evaluation does not run before analysis by surprise. Route explicit metric evaluation or image-folder metrics to [evaluation-metrics](../../evaluation-metrics/SKILL.md).

## Core analysis actions

At least one core action is required. You may combine compatible actions; StudioGAN executes them in the order documented in [checkpoint-analysis-workflows.md](checkpoint-analysis-workflows.md).

| Builder action | Native flag(s) | Data required? | Key constraints | Primary outputs |
| --- | --- | --- | --- | --- |
| `--save-real` | `-sr` / `--save_real_images` | Yes | Needs reference dataset. | `samples/<run_name>/real/<class>/*.png` |
| `--save-fake` | `-sf` / `--save_fake_images` | Usually no | Use `--fake-count` for more than native default. | `samples/<run_name>/fake/<class>/*.png` |
| `--fake-count N` | `-sf_num N` / `--save_fake_images_num N` | No, but requires `--save-fake` | Positive integer. | Number of fake PNGs to save. |
| `--visualize` | `-v` / `--vis_fake_images` | Usually checkpoint/config | Config batch size must be divisible by 8. Provide data if config asserts. | `figures/<run_name>/generated_canvas_<step>.png` |
| `--knn` | `-knn` / `--k_nearest_neighbor` | Yes | No DDP; batch size divisible by 8; may need ResNet50 weights. | KNN grids under `figures/<run_name>/` |
| `--interpolation` | `-itp` / `--interpolation` | Usually no | Only `big_resnet`, `big_resnet_deep_legacy`, `big_resnet_deep_studiogan`; batch size divisible by 8. | Fixed-`z` and fixed-`y` interpolation grids |
| `--frequency` | `-fa` / `--frequency_analysis` | Yes | No DDP; can be memory-heavy. | `figures/<run_name>/dfft_spectrum.png` |
| `--tsne` | `-tsne` / `--tsne_analysis` | Yes | No DDP; can be memory/time-heavy; uses discriminator embeddings. | `tsne_scatter_real.png`, `tsne_scatter_fake.png` |
| `--ifid` | `-ifid` / `--intra_class_fid` | Yes | No DDP; batch size divisible by 8; may need eval backbone weights. | `statistics/<run_name>/iFID.npy` |
| `--gan-train` | `--GAN_train` | Yes | CAS recall; class-conditioned config; no DDP; batch size divisible by 8; long classifier training. | CAS classifier checkpoint and logs |
| `--gan-test` | `--GAN_test` | Yes | CAS precision; mutually exclusive with `--gan-train`; same CAS constraints. | CAS classifier checkpoint and logs |
| `--resume-classifier-train` | `-resume_ct` / `--resume_classifier_train` | Yes | Only meaningful with `--gan-train` or `--gan-test`. | Resumes CAS classifier if checkpoint exists. |
| `--sefa` | `-sefa` / `--semantic_factorization` | Usually no | Requires positive `--sefa-axis`; BigGAN-focused; not StyleGAN2/3. | `figures/<run_name>/*_sefa_images.png` |
| `--sefa-axis K` | `-sefa_axis K` / `--num_semantic_axis K` | No, but requires `--sefa` | `K > 0`; number of semantic rows/axes. | Axis count in SeFa grids. |
| `--sefa-max V` | `-sefa_max V` / `--maximum_variations V` | No, but requires `--sefa` | Larger values make stronger traversals. | Traversal strength. |

## Sampling and statistics modifiers

These flags modify the selected action(s). They are not useful alone.

| Builder modifier | Native flag(s) | Constraints and interpretation |
| --- | --- | --- |
| `--truncation-factor X` | `--truncation_factor X` | `-1` means no truncation. Non-StyleGAN accepts non-negative thresholds. StyleGAN2/3 requires `0 <= X <= 1`. |
| `--truncation-cutoff C` | `--truncation_cutoff C` | Used by StyleGAN W-space sampling to limit which layers receive truncation; ignored by non-StyleGAN generators. |
| `--standing-stats --standing-max N --standing-step S` | `-std_stat -std_max N -std_step S` | Accumulates standing BatchNorm statistics before evaluation/analysis. Use for reliable evaluation on BatchNorm generators when the original training recipe recommends it. |
| `--batch-stat` | `-batch_stat` / `--batch_statistics` | Uses current batch statistics during evaluation. Mutually exclusive with standing statistics. |
| `--langevin` | `-lgv` / `--langevin_sampling` | Applies DDLS/Langevin latent updates during analysis sampling; requires an analysis action and complete Langevin parameters. |
| `--lgv-rate R` | `-lgv_rate R` / `--langevin_rate R` | Initial update rate; must be positive. |
| `--lgv-std S` | `-lgv_std S` / `--langevin_noise_std S` | Gaussian noise standard deviation; must be positive. |
| `--lgv-decay D` | `-lgv_decay D` / `--langevin_decay D` | Optional positive decay strength; use together with `--lgv-decay-steps`. |
| `--lgv-decay-steps N` | `-lgv_decay_steps N` / `--langevin_decay_steps N` | Positive interval for decay; use together with `--lgv-decay`. |
| `--lgv-steps N` | `-lgv_steps N` / `--langevin_steps N` | Total Langevin steps; must be positive. |

## Native compatibility assertions to remember

- Missing checkpoint: analyzing without training requires `-ckpt CKPT_DIR`.
- DDP: visualization, KNN, interpolation, frequency, t-SNE, DDLS/Langevin, SeFa, and CAS are not supported with DDP. Use single GPU or DataParallel.
- Batch size: visualization, KNN, interpolation, iFID, and CAS require `OPTIMIZATION.batch_size % 8 == 0`.
- Interpolation: only Big ResNet-style backbones, not StyleGAN.
- SeFa: `-sefa_axis` must be a natural number greater than 0; StudioGAN's SeFa path is BigGAN-focused.
- Langevin/DDLS: requires `MODEL.z_prior: gaussian`, cannot combine with latent optimization, and must accompany an analysis action.
- CAS: `--GAN_train` and `--GAN_test` are alternative modes; use one at a time. CAS also requires a class-conditioned discriminator config.
- iFID with HDF5: StudioGAN does not support calculating iFID from HDF5 data unless training data is loaded in memory.
- Standing statistics and batch statistics cannot both be enabled.

## Example flag sets

Generated canvas plus fake PNG export:

```bash
python scripts/build_checkpoint_analysis_command.py \
  --repo-root /path/to/PyTorch-StudioGAN \
  --cfg /path/to/config.yaml \
  --checkpoint /path/to/checkpoint-directory \
  --save-dir /path/to/output \
  --gpus 0 \
  --visualize --save-fake --fake-count 64
```

KNN with truncation:

```bash
python scripts/build_checkpoint_analysis_command.py \
  --repo-root /path/to/PyTorch-StudioGAN \
  --cfg /path/to/config.yaml \
  --checkpoint /path/to/checkpoint-directory \
  --save-dir /path/to/output \
  --data-dir /path/to/data \
  --gpus 0 \
  --knn --truncation-factor 0.8
```

BigGAN SeFa:

```bash
python scripts/build_checkpoint_analysis_command.py \
  --repo-root /path/to/PyTorch-StudioGAN \
  --cfg /path/to/biggan-config.yaml \
  --checkpoint /path/to/checkpoint-directory \
  --save-dir /path/to/output \
  --gpus 0 \
  --sefa --sefa-axis 5 --sefa-max 2.0
```

DDLS/Langevin with t-SNE:

```bash
python scripts/build_checkpoint_analysis_command.py \
  --repo-root /path/to/PyTorch-StudioGAN \
  --cfg /path/to/config.yaml \
  --checkpoint /path/to/checkpoint-directory \
  --save-dir /path/to/output \
  --data-dir /path/to/data \
  --gpus 0 \
  --tsne --langevin --lgv-rate 0.1 --lgv-std 0.01 --lgv-steps 10
```
