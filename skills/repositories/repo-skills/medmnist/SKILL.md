---
name: medmnist
description: "Use MedMNIST for standardized 2D and 3D biomedical image dataset
  loading, local NPZ inspection, safe export, and task-aware evaluation
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MedMNIST operating skill

Use this skill when a task names MedMNIST or asks for standardized biomedical
image benchmark datasets, MedMNIST+ resolutions, `.npz` split files, 2D/3D
PyTorch dataset classes, no-PyTorch array access, standard export, or AUC/ACC
evaluation. This is an operating guide for the public `medmnist` package, not
a clinical decision aid and not the external paper-experiment repository.

## Start here

1. Run the safe package diagnostic in [the install overview](references/api-overview.md)
or use `scripts/check_install.py --help` and `scripts/check_install.py` before
claiming the package or its dependencies are ready.
2. Identify the exact dataset flag, task type, split, image size, root, and
whether the input is an official NPZ or a local synthetic fixture. Inspect
`medmnist.INFO[flag]` before interpreting labels.
3. Follow exactly one focused route:

| User intent | Read next |
|---|---|
| Install/import, select a subset, inspect metadata, load 2D/3D data, use splits/sizes/transforms/mmap/RGB, or read NPZ without torch | [`dataset-loading`](sub-skills/dataset-loading/SKILL.md) |
| Compute metrics, prepare score arrays, parse standard result CSVs, export PNG/GIF/CSV, create montages, or use `save`/`evaluate` | [`evaluation-and-export`](sub-skills/evaluation-and-export/SKILL.md) |

4. Keep a separate writable data root and output directory. Do not download
all subsets, delete a default root, run the development-only broad test loop,
or mix real medical data with a synthetic fixture without labeling the source.
5. For a current-checkout question, read [repository provenance](references/repo-provenance.md)
first. If the commit, package metadata, or public entry points differ, request
a repo-skill refresh rather than trusting stale details.

## Installation and baseline check

The public package is installed with:

```bash
python -m pip install medmnist
python -c "import medmnist; print(medmnist.__version__)"
```

The inspected baseline is `3.0.2`. Its documented runtime requirements include
NumPy, pandas, scikit-learn, scikit-image, tqdm, Pillow, Fire, PyTorch, and
torchvision. The selected MedMNIST workflows need only CPU behavior; no CUDA
device is required. For a read-only version/import/registry check, run:

```bash
python scripts/check_install.py
```

Read [the shared API overview](references/api-overview.md) for package object
relationships and the minimal environment contract. Read [shared
troubleshooting](references/troubleshooting.md) for import, dependency, root,
network, data, and medical-use boundaries.

## Operating boundaries

- Use the official Zenodo distribution when obtaining data and preserve the
  published checksum when validating a download. `download=True` is an
  intentional network action, not a harmless import check.
- `root` must exist before dataset/evaluator construction. Prefer an explicit
  project-local or temporary root instead of relying on `~/.medmnist`.
- Always record the exact flag, split, size, task, label shape, and whether the
  file is official or synthetic in a handoff.
- MedMNIST is a benchmark/data API and is **not intended for clinical use**.
  Respect the per-dataset license; DermaMNIST is CC BY-NC 4.0 while the other
  listed subsets are documented as CC BY 4.0.
- Do not infer training, weights, or paper-reproduction workflows from this
  package. The external experiments repository is outside this skill's source
  contract.
