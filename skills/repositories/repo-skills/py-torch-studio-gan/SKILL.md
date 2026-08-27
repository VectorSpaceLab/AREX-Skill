---
name: py-torch-studio-gan
description: "Use PyTorch-StudioGAN for GAN image-synthesis training, YAML
  configuration, checkpoint sampling and analysis, and IS/FID/PRDC evaluation
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# PyTorch-StudioGAN repo skill

Use this skill when a task names **PyTorch-StudioGAN**, **StudioGAN**, `src/main.py`, `src/evaluate.py`, BigGAN/StyleGAN StudioGAN YAML configs, GAN image-synthesis training, checkpoint image analysis, or StudioGAN IS/FID/PRDC metric workflows.

This is a repo-specific operating guide for a **script-first** project. StudioGAN does not expose a normal Python package or console entry point; practical runs use a separate StudioGAN checkout and its `src/main.py` / `src/evaluate.py` scripts. The bundled helpers in this skill accept `--repo-root /path/to/PyTorch-StudioGAN` so they can validate or build commands for whatever checkout the user is actually using.

## Choose the route

| User task | Read next |
| --- | --- |
| Choose or edit YAML configs, validate custom ImageFolder data, build training/resume/freezeD/DDP/HDF5 commands | [training and configuration](sub-skills/training-and-configuration/SKILL.md) |
| Evaluate real/fake image folders with IS, FID, PRDC, cache features/moments, choose eval backbones or clean/friendly resizers | [evaluation metrics](sub-skills/evaluation-metrics/SKILL.md) |
| Use trained checkpoints for fake/real image saving, visualization, KNN, interpolation, frequency analysis, t-SNE, iFID, CAS, SeFa, truncation, or Langevin sampling | [sampling and analysis](sub-skills/sampling-and-analysis/SKILL.md) |
| Check install/runtime assumptions, CUDA, script-first layout, W&B, pretrained weights, or custom CUDA op issues | [root troubleshooting](references/troubleshooting.md) |
| Confirm what source version this skill was distilled from before refreshing | [repository provenance](references/repo-provenance.md) |

## Minimum operating prerequisites

- A StudioGAN checkout with `README.md`, `src/main.py`, `src/evaluate.py`, `src/config.py`, `src/configs/`, `src/models/`, `src/metrics/`, and `src/utils/`.
- Python with PyTorch and TorchVision installed for the user's backend. StudioGAN's real training, sampling, and metric paths are CUDA-oriented; CPU-only environments are suitable for command/config checks only.
- Runtime Python dependencies used by the selected workflows: `tqdm`, `ninja`, `h5py`, `kornia`, `matplotlib`, `pandas`, `scikit-learn` (imports as `sklearn`), `scipy`, `seaborn`, `wandb`, `PyYAML` (imports as `yaml`), `click`, `requests`, `pyspng`, `imageio-ffmpeg`, and `timm`.
- Dataset, checkpoint, pretrained metric weights/cache, W&B login/offline policy, and CUDA toolkit/compiler availability when the selected workflow needs them.

## Fast environment and checkout check

Run the root helper before suggesting a long training or metric job:

```bash
python scripts/check_studiogan_environment.py \
  --repo-root /path/to/PyTorch-StudioGAN \
  --require-cuda \
  --run-cli-help
```

The helper imports the expected dependencies, checks CUDA when requested, verifies that the checkout has the two public scripts, and can run `-h` help checks without training, downloading data, or contacting W&B.

## Common safe workflow pattern

1. Start with [training and configuration](sub-skills/training-and-configuration/SKILL.md) to validate the YAML and data layout.
2. Build a dry-run training command; do not launch long runs until GPU count, W&B policy, save directory, and dataset availability are clear.
3. After a checkpoint exists, use [sampling and analysis](sub-skills/sampling-and-analysis/SKILL.md) for checkpoint-driven outputs or [evaluation metrics](sub-skills/evaluation-metrics/SKILL.md) for standalone folder metrics.
4. If a command fails, prefer the nearest troubleshooting reference before changing configs by guesswork.

## Do not over-claim verification

- CLI help, config validation, and bundled command-builder checks prove wiring and option compatibility; they do not prove benchmark-quality GAN training or meaningful metric values.
- Tiny image folders are useful for input-shape smoke tests only; they do not produce meaningful FID/PRDC/IS.
- Long training, model-weight downloads, W&B network login, TensorFlow 1.x legacy metrics, and first-time StyleGAN custom-op compilation require explicit runtime budget and environment approval.

## Router metadata

Structured router metadata for managed import lives in [repo routing metadata](references/repo-routing-metadata.json). Do not hand-edit a live router from this skill tree.
