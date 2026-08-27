---
name: biggan-pytorch
description: "Guides CUDA-based BigGAN-PyTorch training, checkpoint sampling,
  dataset preparation, metric preparation, model customization, and optional
  TensorFlow Hub weight conversion."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# BigGAN-PyTorch

Use this skill for the author's unofficial PyTorch implementation of BigGAN and
its adjacent BigGAN-deep, CIFAR, ImageNet/HDF5, sampling, metric, and TFHub
conversion workflows. This is a research codebase rather than an installable
library: run its entry points from a checkout, keep outputs outside source
files, and treat long training and downloads as explicit user-approved work.

## Route the request

- **Training, fine-tuning, architecture or optimizer changes, checkpoint
  resume, multi-GPU, EMA, spectral norm, or mixed precision:** read
  `sub-skills/training/SKILL.md` and its references.
- **Generate images, load a checkpoint, use EMA, standing statistics,
  truncation curves, NPZ export, sample sheets, IS, or FID:** read
  `sub-skills/sampling/SKILL.md`.
- **Prepare ImageFolder/CIFAR data, convert ImageNet to HDF5, validate HDF5, or
  calculate Inception moments:** read `sub-skills/data-preparation/SKILL.md`.
- **Port DeepMind TFHub BigGAN weights:** read
  `sub-skills/tfhub-conversion/SKILL.md`; this route is reference-only unless
  legacy TensorFlow 1.x, TensorFlow Hub, network access, and compatible GPU
  support are deliberately provisioned.

Read `references/model-overview.md` for the verified model/data matrix and
`references/troubleshooting.md` for cross-cutting failures. Read
`references/repo-provenance.md` before relying on version-sensitive details or
planning a refresh.

## Environment and invocation

The repository has no packaging metadata or console entry point. Use a Python
environment with a CUDA-capable PyTorch/torchvision pair plus NumPy, SciPy,
h5py, Pillow, and tqdm. The README documents an old PyTorch 1.0.1 baseline;
the core modules were import-checked and a tiny CUDA generator forward pass was
verified with a modern compatible PyTorch installation. Do not assume every
legacy option works unchanged on a new PyTorch release.

Set `SKILL_ROOT` to the directory containing this file and `REPO_ROOT` to the
checked-out BigGAN-PyTorch repository. Repository entry points run from
`REPO_ROOT`; bundled skill helpers are invoked through their `SKILL_ROOT`
paths:

```bash
SKILL_ROOT=/path/to/skills/disco/biggan-pytorch
REPO_ROOT=/path/to/BigGAN-PyTorch
cd "$REPO_ROOT"
python "$SKILL_ROOT/scripts/check_environment.py" --repo-root "$REPO_ROOT"
```

Other repository entry points can then be run from the same checkout, for
example:

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
python train.py --dataset C10 --num_epochs 1 --batch_size 8
python sample.py --dataset C10 --experiment_name <name> --load_weights best0
```

The entry points hard-code `cuda` in training, sampling, metric,
interpolation, and several utility paths. A CPU import is useful for static
inspection but is not evidence that the operational workflows work. The
environment helper above is intentionally diagnostic; it does not download
data, modify checkpoints, or launch training.

## Shared operational rules

1. Decide the dataset and resolution first. Dataset names (`I32`, `I64`,
   `I128`, `I256`, their `_hdf5` variants, `C10`, and `C100`) determine image
   size, class count, root name, and model output shape.
2. Keep `data_root`, `weights_root`, `logs_root`, and `samples_root` explicit.
   `base_root` can re-root the four locations, but parent directories must
   already exist when the code creates child directories.
3. Use the launch recipes as parameter references, not as unattended jobs.
   ImageNet preparation, TFHub downloads, full sampling metrics, and training
   are expensive or network-dependent.
4. Record the exact model module (`BigGAN` or `BigGANdeep`), latent settings,
   class count, EMA choice, and checkpoint suffix with every result.
5. Do not compare this repository's PyTorch Inception scores/FID directly with
   official TensorFlow metrics; read the sampling and metric references.

The bundled scripts are safe diagnostics or validators. They do not replace the
repository's full training/data entry points; pass an explicit `--repo-root`
when a diagnostic needs to import the checked-out model. They never download
data, mutate checkpoints, or launch a production run by default.
