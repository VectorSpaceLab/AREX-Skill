---
name: geoseg
description: "Guide GeoSeg remote-sensing semantic-segmentation data
  preparation, model/config selection, supervised training, benchmark
  evaluation, UAVid inference, and huge-image prediction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# GeoSeg

Use this operating graph for the `WangLibo1995/GeoSeg` toolbox: a PyTorch and
PyTorch Lightning toolkit for semantic segmentation of remote-sensing imagery.
It covers four connected routes without assuming that datasets, pretrained
weights, or checkpoints are present.

## Route by task

- **Prepare data or repair labels:** read
  [data-preparation](sub-skills/data-preparation/SKILL.md). It owns LoveDA mask
  conversion and ISPRS/UAVid patch splitting, layouts, class encodings, and
  pair/shape validation.
- **Choose a model or inspect a config:** read
  [model-and-config](sub-skills/model-and-config/SKILL.md). It owns model
  families, dataset class counts, losses, auxiliary outputs, optimizer and
  checkpoint fields, and static config inspection.
- **Train a configured model:** read
  [training](sub-skills/training/SKILL.md) after data and config preflight. It
  owns the Lightning module, training CLI, metrics, checkpoint intent, and
  resume/pretrain decisions.
- **Evaluate tiles or infer images:** read
  [evaluation-inference](sub-skills/evaluation-inference/SKILL.md). It owns
  Vaihingen/Potsdam/LoveDA evaluation, UAVid sequence inference, huge-image
  tiling/stitching, TTA, and mask output formats.

For a request spanning routes, use them in this order: data preparation →
model/config → training or evaluation/inference. Do not treat preprocessing
success as evidence that a model checkpoint or CUDA inference path works.

## Environment and source contract

GeoSeg has no `pyproject.toml`, `setup.py`, or console entry-point metadata in
the captured repository. Use a checkout of the project as the source tree and
run the bundled wrappers with an explicit `--repo-root`; do not assume the
current directory is the checkout. The repository README documents Python 3.8,
CUDA-oriented PyTorch installation, `requirements.txt`, and optional
`causal-conv1d`/`mamba-ssm` for PyramidMamba. The verified core inspection stack
used torch 2.0.1+cu118, torchvision 0.15.2+cu118, pytorch-lightning 2.3.0,
timm 0.9.16, albumentations 1.3.1, ttach, catalyst for legacy inference
imports, and scikit-image for huge-image imports.

Start with a private environment and install a CUDA-compatible PyTorch wheel
for actual training/inference. The root requirements file contains both
`lightning` and `pytorch-lightning`; source code imports `pytorch_lightning`.
If the `lightning` meta-package conflicts with its resolved pydantic stack,
keep the source-used `pytorch-lightning` path and record the omitted redundant
package rather than changing source imports. `PyramidMamba` additionally needs
`mamba_ssm`; treat that backend as optional until it is installed and smoked.

Run the bundled diagnostics before a workflow when the environment is unclear:

```bash
python <path-to-this-skill>/scripts/check_env.py
python <path-to-this-skill>/scripts/metric_smoke.py
python <path-to-this-skill>/scripts/run_geoseg_entrypoint.py \
  --wrapper-help
```

`check_env.py` verifies core imports and a tiny CUDA allocation without
importing data-bound configs; `metric_smoke.py` exercises the metric equations;
`run_geoseg_entrypoint.py` forwards a supported native entry point from an
explicit user checkout. These helpers do not download data, weights, or
checkpoints.

## Shared safety rules

- Acquire LoveDA, ISPRS, UAVid data and pretrained/checkpoint files separately;
  do not infer availability from config names.
- Keep raw data, processed patches, RGB visualization masks, checkpoints, and
  logs in distinct directories. Validate exact image/mask stems, shapes, label
  values, and dataset class order before training.
- Config modules execute top-level code and may enumerate data or load weights;
  use the static inspectors in the sub-skills before importing them.
- Training and inference entry points call CUDA methods. CPU checks cover
  preprocessing, metrics, and static API guidance only; they do not verify
  GPU-required execution.
- Avoid full training, benchmark-scale inference, downloads, and external
  submissions during routine diagnosis. Record the data, weight, backend, and
  compute limits that prevented a run.
- Read [troubleshooting.md](references/troubleshooting.md) for cross-cutting
  installation, import, path, config, checkpoint, CUDA, and output failures.
- Read [repo-provenance.md](references/repo-provenance.md) before deciding that
  this graph matches a changed checkout; refresh it when the commit, public
  entry points, or evidence paths differ.

## Verification boundary

The source snapshot had no datasets, model weights, native tests, notebooks, or
examples beyond the README, configs, tools, and root scripts. Core imports,
API signatures, and a CUDA allocation were inspected in an isolated Python 3.8
runtime; LoveDA's data-bound import and PyramidMamba's optional extension
remain explicit prerequisites. Full native train/evaluation/inference runs are
not claimed until real data, compatible checkpoints, and CUDA execution are
available.
