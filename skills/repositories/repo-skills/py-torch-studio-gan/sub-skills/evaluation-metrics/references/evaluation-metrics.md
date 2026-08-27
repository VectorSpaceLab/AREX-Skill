# Evaluation metrics overview

StudioGAN exposes metric workflows in two places:

1. **Standalone image-folder evaluation** through `python src/evaluate.py`, for comparing a real/reference ImageFolder (`--dset1`) or cached real statistics against a generated/target ImageFolder (`--dset2`). This is the focus of this sub-skill.
2. **Training/checkpoint evaluation** through `python src/main.py`, where `-metrics/--eval_metrics`, `-ifid`, `--GAN_train`, and `--GAN_test` are attached to a StudioGAN config/checkpoint workflow. Use this page for metric semantics, then route command construction and config/data preparation to sibling sub-skills when needed.

## Metric names and outputs

| User-facing metric | StudioGAN flag or path | Output keys/signals | Notes |
| --- | --- | --- | --- |
| Inception Score | `-metrics is` | `IS`, plus `Top1_acc`/`Top5_acc` when the evaluation path enables ImageNet-style accuracy | Standalone folder evaluation computes dset2 IS and does not use ten splits. |
| Frechet Inception Distance | `-metrics fid` | `FID` | Requires reference moments from `--dset1` or `--dset1_moments`. Tiny datasets can produce singular or unstable covariance. |
| Improved precision and recall | `-metrics prdc` | `Improved_Precision`, `Improved_Recall` | Uses PRDC feature manifolds with nearest-k fixed to 5 in the standalone evaluator. |
| Density and coverage | `-metrics prdc` | `Density`, `Coverage` | Computed by the same PRDC code path as improved precision/recall. |
| Intra-class FID | `python src/main.py -ifid` | `iFID` records | Checkpoint/config workflow only. It loops over classes, uses reference class images, and generates class-conditional fake images. |
| Classifier Accuracy Score | `python src/main.py --GAN_train` or `--GAN_test` | classifier top-k records | Checkpoint/config workflow only. `--GAN_train` estimates recall; `--GAN_test` estimates precision. It is class-conditional and not supported with DDP. |

StudioGAN's public docs describe clean metrics, architecture-friendly metrics, and multiple backbones. The actual implemented standalone evaluator accepts the metrics `is`, `fid`, and `prdc`; `prdc` covers improved precision/recall plus density/coverage.

## Standalone image-folder evaluation workflow

Use this when the user already has folders of real/reference images and generated/target images.

1. Confirm both folders are ImageFolder-like: `root/class_name/image.*`, with at least one class subdirectory. A single dummy class name is acceptable for generated images if labels are irrelevant.
2. Choose metrics:
   - `fid` by default when the user asks for FID only.
   - `is fid prdc` for the common full report.
   - Avoid `none` for standalone evaluation; it is mainly useful in training commands to skip metric work.
3. Decide whether to use cached reference inputs:
   - No cache: pass `--dset1` and StudioGAN extracts reference features/moments.
   - FID cache only: pass `--dset1_moments` for FID, but still pass `--dset1` if PRDC is also requested and no feature cache is available.
   - PRDC cache only: pass `--dset1_feats` for PRDC, but still pass `--dset1` if FID is also requested and no moment cache is available.
   - Full cache with no real folder: pass both `--dset1_feats` and `--dset1_moments`.
4. Choose `--eval_backbone` and `--post_resizer` together. See [backbones, resizers, and caches](backbones-resizers-and-caches.md).
5. Build a dry-run command with [the command builder](../scripts/evaluate_image_folders_command.py), then run the emitted command only when the user has approved GPU and pretrained-weight/cache requirements.

## Training-time metrics through `src/main.py`

`python src/main.py` uses the same public metric names through `-metrics/--eval_metrics`:

```bash
CUDA_VISIBLE_DEVICES=0 python src/main.py -t -metrics is fid prdc -cfg CONFIG_PATH -data DATA_PATH -save SAVE_PATH
```

Relevant facts for future agents:

- `-metrics` accepts `is`, `fid`, `prdc`, or `none`.
- FID reference moments are prepared under the run's moments cache and reused when possible.
- PRDC reference features are prepared under the run's features cache and reused when possible.
- `--eval_backbone` and `--post_resizer` apply to training-time metrics as well as standalone folder evaluation.
- Training/checkpoint metrics require the config, dataset, checkpoint, save directory, CUDA environment, and sometimes W&B settings; route those details to [training and configuration](../../training-and-configuration/SKILL.md).

## iFID and CAS connections

These are not exposed by `src/evaluate.py`.

- **iFID** (`-ifid`) is a checkpoint/config analysis mode in `src/main.py`. It calculates per-class FID using the training/reference dataset class partitions and generated samples for each class. It is meaningful only for class-conditional runs with enough per-class data. It is incompatible with some HDF5 modes unless data is loaded in memory.
- **CAS** (`--GAN_train`, `--GAN_test`) trains/evaluates a classifier as a generative-model precision/recall proxy. It requires class-conditional GAN settings, is not supported with DDP, and can be long-running. Route CAS execution questions to [sampling and analysis](../../sampling-and-analysis/SKILL.md) after explaining the metric meaning.

## Verification boundary

Construction-time checks verified the CLI surfaces and representative configuration compatibility, not full metric values. Full IS/FID/PRDC/iFID/CAS values require real data scale, cached or downloadable pretrained weights, and GPU execution.
