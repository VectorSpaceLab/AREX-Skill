---
name: sampling-and-analysis
description: "Use trained StudioGAN checkpoints for sampling, visual analysis,
  memorization checks, latent studies, CAS, iFID, SeFa, truncation, and
  Langevin/DDLS-aware command construction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Sampling and Analysis

Use this sub-skill when a user already has a trained StudioGAN checkpoint and asks to sample images, save real/fake image folders, visualize generated canvases, check memorization with KNN, run latent interpolation, inspect frequency spectra, plot t-SNE embeddings, compute intra-class FID, run CAS, explore SeFa axes, or apply truncation/Langevin sampling during checkpoint analysis.

## Route first

- For dataset preparation, config selection, training, HDF5 setup, or producing the checkpoint in the first place, route to [training-and-configuration](../training-and-configuration/SKILL.md).
- For standalone image-folder metrics through `src/evaluate.py`, route to [evaluation-metrics](../evaluation-metrics/SKILL.md).
- For checkpoint-driven outputs through `src/main.py`, stay here and read the workflow references below.

## Required runtime context

A future agent should have:

1. A separate StudioGAN checkout, referred to as `/path/to/PyTorch-StudioGAN`.
2. The exact YAML config family used for the checkpoint.
3. A checkpoint directory containing StudioGAN model files, preferably both best and current G/D checkpoint names.
4. A save directory for analysis outputs.
5. A dataset/reference directory when running real-image, KNN, frequency, t-SNE, iFID, or CAS workflows.

Do not use DDP for these analyses. StudioGAN supports many of them only with a single visible GPU or DataParallel; the bundled command builder intentionally has no DDP option.

## Start with the bundled command builder

Use [scripts/build_checkpoint_analysis_command.py](scripts/build_checkpoint_analysis_command.py) to build, validate, and print a native `python /path/to/PyTorch-StudioGAN/src/main.py ...` command without executing it. The helper suppresses default FID evaluation with `-metrics none` so visual/sampling analyses do not unexpectedly run long metric jobs.

Example command construction:

```bash
python scripts/build_checkpoint_analysis_command.py \
  --repo-root /path/to/PyTorch-StudioGAN \
  --cfg src/configs/CIFAR10/ContraGAN.yaml \
  --checkpoint /path/to/checkpoints/run-name \
  --save-dir /path/to/analysis-output \
  --data-dir /path/to/data \
  --gpus 0 \
  --visualize --save-fake --fake-count 64 \
  --truncation-factor 0.7
```

Then inspect the printed command, adjust paths if needed, and run it from a shell only after confirming that its output directory is safe to use.

## Read these references

- [Checkpoint analysis workflows](references/checkpoint-analysis-workflows.md): end-to-end recipes, checkpoint prerequisites, analysis ordering, output locations, and interpretation guidance.
- [Analysis flags reference](references/analysis-flags-reference.md): exact builder flags, native `src/main.py` flags, requirements, incompatibilities, and outputs.
- [Troubleshooting](references/troubleshooting.md): common checkpoint, data, DDP, batch-size, StyleGAN, SeFa, CAS, metric-backbone, and output-directory failures.

## Quick decision guide

| User intent | Use | Must have data? | Main output |
| --- | --- | --- | --- |
| Save generated PNGs for another tool | `--save-fake --fake-count N` | Usually no | `samples/<run_name>/fake/<class>/*.png` |
| Save reference PNGs | `--save-real` | Yes | `samples/<run_name>/real/<class>/*.png` |
| Make a generated-image canvas | `--visualize` | Usually checkpoint/config; pass data if config asserts | `figures/<run_name>/generated_canvas_<step>.png` |
| Check memorization against real images | `--knn` | Yes | `figures/<run_name>/fake_anchor_*NN_*_classes.png` |
| Interpolate latent/class directions | `--interpolation` | Usually no | `figures/<run_name>/*_Interpolated_images_*.png` |
| Compare real/fake frequency spectra | `--frequency` | Yes | `figures/<run_name>/dfft_spectrum.png` |
| Plot discriminator embedding t-SNE | `--tsne` | Yes | `figures/<run_name>/tsne_scatter_real.png`, `tsne_scatter_fake.png` |
| Intra-class diversity | `--ifid` | Yes | `statistics/<run_name>/iFID.npy` plus logs |
| CAS recall/precision | `--gan-train` or `--gan-test` | Yes | classifier checkpoints and top-1/top-5 logs |
| Semantic axes | `--sefa --sefa-axis K --sefa-max V` | Usually no | `figures/<run_name>/*_sefa_images.png` |

## High-risk prompts

If a user asks for interpolation on a StyleGAN2/StyleGAN3 checkpoint, do not try to force it: StudioGAN rejects interpolation outside Big ResNet-style backbones. If a user asks for DDP with KNN and Langevin/DDLS, route them to a single visible GPU or DataParallel command and keep `-DDP` out of the analysis command.
