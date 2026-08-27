---
name: nitrain
description: "Routes Nitrain medical-imaging dataset, preprocessing, training,
  and prediction workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Nitrain

Nitrain is a framework-agnostic Python library for medical-imaging datasets,
image transforms, sampling, model training, and prediction. Use this skill when
users ask about `Dataset`, `Loader`, `Trainer`, `Predictor`, ANTsPy-based image
workflows, or the package-level APIs exposed by `nitrain`.

## Install at a glance

Read [references/installation.md](references/installation.md) for the
verified CPU stack, workflow-specific pins, and the small set of packages that
cover the inspected workflows.

For a quick import check from an installed environment:

```bash
python -c "import nitrain as nt; print(nt.__version__); from nitrain import readers, transforms, samplers; print(readers.ImageReader, transforms.RangeNormalize, samplers.SliceSampler)"
```

For a broader smoke check, run [scripts/check_install.py](scripts/check_install.py):

```bash
python scripts/check_install.py --mode all
```

Use `--mode base`, `--mode datasets`, `--mode preprocess`, `--mode models`,
`--mode predictor`, or `--mode torch` if you only want one workflow family.

## Route map

### [sub-skills/datasets-readers/SKILL.md](sub-skills/datasets-readers/SKILL.md)
Use this route when you need to build datasets from local files, CSV/TSV
columns, folder labels, in-memory arrays or images, nested reader structures,
example data, or Google Cloud storage.

Typical requests:
- "Create a dataset from images and participants.csv"
- "Infer readers from nested lists or dictionaries"
- "Load the built-in example-01 fixture"
- "Use a Google Cloud bucket as a dataset source"

Read [sub-skills/datasets-readers/SKILL.md](sub-skills/datasets-readers/SKILL.md) when the task is about data layout, reader choice, or missing-file / credential errors.

### [sub-skills/preprocessing-and-loading/SKILL.md](sub-skills/preprocessing-and-loading/SKILL.md)
Use this route when you need to apply transforms, compose random augmentations,
choose samplers, or batch data with `Loader` and `Loader.to_keras()`.

Typical requests:
- "Add aligned transforms to inputs and outputs"
- "Sample slices, patches, or blocks"
- "Make a Keras-ready loader"
- "Explain why a transform key or sampler shape failed"

Read [sub-skills/preprocessing-and-loading/SKILL.md](sub-skills/preprocessing-and-loading/SKILL.md) when the task is about shape changes, augmentation pipelines, or loader batching.

### [sub-skills/models-training/SKILL.md](sub-skills/models-training/SKILL.md)
Use this route when you need to discover architectures, list available model
families, fetch pretrained weights, or train/evaluate Keras/TensorFlow or
Torch/MONAI models with Nitrain trainers.

Typical requests:
- "Create an ANTsPyNet model"
- "List supported architectures"
- "Train a regression model with Trainer"
- "Run the TorchTrainer CPU path"

Read [sub-skills/models-training/SKILL.md](sub-skills/models-training/SKILL.md) when the task is about model construction, trainer defaults, metrics, saving, or framework detection.

### [sub-skills/prediction-and-explanation/SKILL.md](sub-skills/prediction-and-explanation/SKILL.md)
Use this route when you need to run slice-based prediction with `Predictor` or
inspect the current `OcclusionExplainer` surface.

Typical requests:
- "Predict segmentation outputs from a Dataset"
- "Reconstruct slice predictions into ANTs images"
- "Check what OcclusionExplainer does right now"

Read [sub-skills/prediction-and-explanation/SKILL.md](sub-skills/prediction-and-explanation/SKILL.md) when the task is about inference output shape, slice-axis handling, or the explainer stub.

## Common prerequisites

- `antspyx` is the core imaging dependency.
- `pandas` is needed for CSV/TSV-backed readers.
- `antspynet`, `tensorflow`, and `tf-keras` are needed for the verified
  Keras/TensorFlow model and trainer workflows.
- `torch` and `monai` are needed for the CPU TorchTrainer smoke path.
- `google-cloud-storage` and `google-auth` are needed for GCS-backed datasets.
- `datalad` and `git-annex` are only needed for networked OpenNeuro-style fetches.

## Public quirks worth remembering

- `nitrain.fetch_pretrained` is a submodule object in this snapshot; import the
  callable from `nitrain.models.fetch_pretrained`.
- `TorchTrainer` is available from `nitrain.trainers`, not from the package root.
- The README still mentions `tx.RandomNoise`, but that transform is not present
  in the inspected source tree.
- TensorFlow may print harmless CPU-only warnings on hosts without CUDA.

## When to read the supporting references

- [references/installation.md](references/installation.md) — the verified
  install matrix and the safest package pins for this snapshot.
- [references/troubleshooting.md](references/troubleshooting.md) —
  cross-cutting import, version, and backend issues that affect several
  workflows.
- [references/repo-provenance.md](references/repo-provenance.md) — confirm
  whether this skill still matches the current checkout before you reuse it or
  refresh it.
- [scripts/check_install.py](scripts/check_install.py) — run this to verify
  the package and the selected workflow family without reopening the source
  checkout.

## How to think about the package

Nitrain is best treated as four user-facing workflow families:

1. dataset and reader construction,
2. preprocessing and loading,
3. model discovery and training,
4. prediction and the current explainer surface.

Each family has its own sub-skill because the package combines imaging data
layout, transforms, samplers, model backends, and output post-processing in a
way that is easier to use when routed separately.

## Before you refresh or reuse this skill

If the current repository commit, package version, or exported API surface has
changed, this skill may be stale. Read `references/repo-provenance.md` first,
then refresh the skill instead of assuming the guidance still matches the code.
