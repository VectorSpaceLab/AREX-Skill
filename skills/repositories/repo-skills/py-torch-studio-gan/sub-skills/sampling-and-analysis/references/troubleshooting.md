# Sampling and Analysis Troubleshooting

## Purpose

Use this when a StudioGAN checkpoint-analysis command fails before or during sampling, visualization, KNN, interpolation, frequency analysis, t-SNE, iFID, CAS, SeFa, truncation, or Langevin/DDLS sampling.

Start by rebuilding the command with [../scripts/build_checkpoint_analysis_command.py](../scripts/build_checkpoint_analysis_command.py). It catches many failures before the native command runs.

## Failure matrix

| Symptom or error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `Specify -ckpt CHECKPOINT_FOLDER to evaluate GAN without training.` | The command is analyzing without `-t` but no checkpoint directory was supplied. | Add `--checkpoint /path/to/checkpoint-directory` to the builder, or native `-ckpt /path/to/checkpoint-directory`. |
| `list index out of range` while loading G/D checkpoints, or no checkpoint path is logged | The checkpoint directory does not contain the expected StudioGAN file names. | Inspect the checkpoint directory for `model=G-best-weights-step=*.pth`, `model=D-best-weights-step=*.pth`, and current G/D files. Use the directory path, not a single `.pth` file. If only current files exist, expect final best-checkpoint reload to fail. |
| `Missing key(s)` / `Unexpected key(s)` / tensor shape mismatch during checkpoint loading | Config and checkpoint family do not match. | Use the YAML config from the same model family, dataset, resolution, conditioning method, and backbone as the checkpoint. Do not analyze BigGAN checkpoints with StyleGAN configs or vice versa. |
| Command works until final analysis reload, then fails on `model=G-best...` or `model=D-best...` | StudioGAN reloads the best checkpoint before final analyses, even after initial current-checkpoint loading. | Provide a checkpoint directory with best G/D files. If the training run never saved a best checkpoint, rerun or repair the checkpoint set before analysis. |
| DDP assertion: `StudioGAN does not support image visualization, k_nearest_neighbor, interpolation, frequency, tsne analysis, DDLS, SeFa, and CAS with DDP.` | Analysis command included `-DDP` or a previous command pattern was copied from training. | Remove `-DDP`, `-tn`, and `-cn`. Use one visible GPU (`CUDA_VISIBLE_DEVICES=0`) or expose multiple GPUs for DataParallel only when memory requires it. The bundled builder never emits DDP flags. |
| `Cannot perform distributed training with a single gpu.` | `-DDP` was passed while only one GPU is visible. | Same as above: remove DDP for analysis. |
| `batch_size should be divided by 8.` | Visualization, KNN, interpolation, iFID, or CAS was requested with `OPTIMIZATION.batch_size` not divisible by 8. | Edit or choose a matching config whose batch size is a multiple of 8, then rebuild the command. Keep the config/checkpoint family compatible. |
| Interpolation assertion: `does not support interpolation analysis except for biggan and big_resnet_deep backbones` | User requested interpolation for an unsupported backbone, commonly StyleGAN2/StyleGAN3. | Do not force interpolation. Use `--visualize`, `--save-fake`, truncation, or StyleGAN-supported analyses instead. For interpolation, use a checkpoint whose config backbone is `big_resnet`, `big_resnet_deep_legacy`, or `big_resnet_deep_studiogan`. |
| StyleGAN assertion mentions unsupported options with `interpolation` or `semantic_factorization` | StyleGAN2/StyleGAN3 config rejects those analysis options. | Remove `--interpolation` and `--sefa`. Use StyleGAN truncation (`--truncation-factor` between 0 and 1, optionally `--truncation-cutoff`) plus visualization/save-fake workflows. |
| SeFa assertion: `set num_semantic_axis to a natural number greater than 0` | `-sefa` was used without a positive `-sefa_axis`. | Use builder flags `--sefa --sefa-axis K --sefa-max V` with `K > 0`. SeFa is BigGAN-focused; avoid it for StyleGAN checkpoints. |
| SeFa fails with missing generator attribute such as `linear0` | The selected backbone is not compatible with StudioGAN's SeFa implementation. | Treat SeFa as BigGAN-focused. Use a Big ResNet/BigGAN-family config and matching checkpoint, or choose another qualitative analysis. |
| `Please specify data_dir...` or dataset loader failures | The workflow needs reference data, or config compatibility requests `-data`. | Provide `--data-dir /path/to/data`. KNN, frequency, t-SNE, iFID, CAS, and save-real require it. Visualization and SeFa mostly sample from the checkpoint but may still hit config-level data assertions in current StudioGAN. |
| KNN/frequency/t-SNE/iFID has no real data or class labels | The selected dataset directory does not match the config's dataset and class layout. | Route data/config setup to [training-and-configuration](../../training-and-configuration/SKILL.md). Confirm dataset name, number of classes, and reference split before rerunning analysis. |
| KNN stalls or fails while loading ResNet50 | KNN uses a ResNet50 feature extractor path that may need cached/downloadable weights. | Use a network-enabled/cache-prepared environment, or skip KNN and use save-fake/visual inspection. Do not promise KNN can run offline unless weights are already cached. |
| iFID or metric-backed analysis tries to download weights or is very slow | Evaluation backbones and feature models may require cached/downloadable weights; per-class loops are expensive. | Warn the user, confirm runtime/network budget, or choose lighter outputs (`--save-fake`, `--visualize`). Standalone image-folder metrics belong in [evaluation-metrics](../../evaluation-metrics/SKILL.md). |
| t-SNE runs out of memory or is too slow | t-SNE stores discriminator embeddings for real and fake batches and can be expensive on large datasets. | Use a smaller compatible dataset/config when possible, run on a machine with more memory, or prefer save-fake/visualization. Remember that StudioGAN randomly limits plots to 10 classes when there are more than 10. |
| `You can't turn on batch_statistics and standing_statistics simultaneously.` | Both `-batch_stat` and `-std_stat` were selected. | Choose one. Use `--standing-stats --standing-max N --standing-step S` for standing BatchNorm statistics, or `--batch-stat` for current batch statistics. |
| Truncation assertion for non-StyleGAN | `--truncation_factor` was negative other than `-1`. | Use `-1` for no truncation or a non-negative value. |
| Truncation assertion for StyleGAN | StyleGAN truncation was outside `[0, 1]`. | Use `--truncation-factor` between 0 and 1. Use `--truncation-cutoff` only when you intentionally want layer-limited StyleGAN W-space truncation. |
| Langevin assertion: `Langevin sampling and latent optimization cannot be used simultaneously` | The config has latent optimization enabled (`LOSS.apply_lo`) and the command uses `-lgv`. | Do not combine them. Choose a non-LO config/checkpoint for Langevin/DDLS or remove `--langevin`. |
| Langevin assertion: `z_prior is gaussian` | The config uses a non-Gaussian latent prior. | Use a checkpoint/config with `MODEL.z_prior: gaussian`, or remove Langevin/DDLS sampling. |
| Langevin command does nothing useful or native parser exits help | `-lgv` was selected without an actual analysis action. | Pair `--langevin` with `--visualize`, `--save-fake`, `--knn`, `--tsne`, or another compatible action, and provide `--lgv-rate`, `--lgv-std`, and `--lgv-steps`. |
| CAS assertion: classifier score undefined for unconditioned GAN | `--GAN_train` or `--GAN_test` was used with `MODEL.d_cond_mtd: W/O`. | Use CAS only with class-conditioned GAN checkpoints. For unconditional checkpoints, use visual, save-fake, FID/PRDC, or other non-class-conditional analyses. |
| CAS runs for a long time or writes classifier checkpoints | CAS trains/evaluates a classifier rather than only sampling images. | Confirm budget before running. Use `--resume-classifier-train` only when a compatible previous CAS classifier checkpoint exists. |
| Output folders unexpectedly replaced | StudioGAN's PNG export recreates `samples/<run_name>/real` or `samples/<run_name>/fake` before saving. | Use a fresh `--save-dir`, or copy existing sample folders before running `--save-real` or `--save-fake`. The command builder itself is non-destructive; the native command can write and replace analysis outputs. |
| Expected figures are missing | An earlier selected analysis failed, or output went under the checkpoint's saved run name rather than the newly constructed run name. | Check logs under `logs/<run_name>.log`. Remember execution order: an earlier failure prevents later selected analyses. Search `figures/<run_name>/`, `samples/<run_name>/`, and `statistics/<run_name>/` under the selected save directory. |
| `wandb` warnings or service-related noise | StudioGAN imports and finishes wandb even for analysis; project/entity are optional. | Usually safe to ignore if the command continues. If an environment forces online logging, configure wandb outside this skill or run in an offline/disabled mode approved by the user. |

## Two difficult cases

### StyleGAN2 interpolation request

If the user asks: "interpolate my StyleGAN2 checkpoint," explain that StudioGAN's checkpoint interpolation path is Big ResNet-only. Offer alternatives:

- generated canvases: `--visualize`;
- class-organized fake PNGs: `--save-fake --fake-count N`;
- StyleGAN truncation: `--truncation-factor 0.5` and optional `--truncation-cutoff`;
- standalone metrics through [evaluation-metrics](../../evaluation-metrics/SKILL.md) if the user has image folders.

Do not edit the config to force `--interpolation`; that produces a compatibility assertion or misleading output.

### DDP plus KNN and Langevin/DDLS request

If the user asks for DDP with KNN and Langevin, split the issue:

1. DDP is not supported for KNN, DDLS/Langevin, or most visual analyses.
2. KNN needs reference data and may need ResNet50 weights.
3. Langevin needs a Gaussian prior, no latent optimization, and positive `-lgv_*` parameters.

Build a single-GPU or DataParallel command instead, for example with `--gpus 0 --knn --langevin --lgv-rate R --lgv-std S --lgv-steps N --data-dir /path/to/data`. If the user truly requires distributed processing, report that this StudioGAN analysis path does not support it rather than silently adding `-DDP`.
