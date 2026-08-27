# Repository Provenance

schema: `disco.repo-provenance.v1`

## Source Snapshot

- Skill id: `nnunetv2`
- Project name in package metadata: `nnunetv2`
- Public project name: nnU-Net v2
- Package version: `2.8.0`
- Source commit: `c65537bebc5b50356df5dad352474bc3389e5e8b`
- Branch: `master`
- Exact tag: `v2.8.0`
- Remote URL: `https://github.com/MIC-DKFZ/nnUNet.git`
- Working tree state at generation: dirty checkout with untracked DisCo outputs and one untracked top-level file named `=0.19.3`.

## Evidence Paths

Runtime skill content was derived from these relative paths:

- `pyproject.toml`, `setup.py`, `nnunetv2.egg-info/`
- `readme.md`, `LICENSE`, `CONTRIBUTING.md`
- `documentation/`
- `nnunetv2/`
- `nnunetv2/dataset_conversion/`
- `nnunetv2/experiment_planning/`
- `nnunetv2/preprocessing/`
- `nnunetv2/run/`
- `nnunetv2/training/`
- `nnunetv2/inference/`
- `nnunetv2/evaluation/`
- `nnunetv2/postprocessing/`
- `nnunetv2/ensembling/`
- `nnunetv2/model_sharing/`
- `nnunetv2/imageio/`
- `nnunetv2/utilities/`
- `nnunetv2/tests/`

## Installed Package Facts Verified During Generation

- `nnunetv2` imports successfully.
- Distribution metadata reports version `2.8.0`.
- Core modules `nnunetv2.paths`, `nnunetv2.utilities.find_class_by_name`, and `torch` import successfully in the private inspection environment.
- Selected console-script help checks passed for planning, training, inference, evaluation, conversion, and best-configuration commands.
- Representative signatures were inspected for `extract_fingerprints`, `preprocess`, `run_training`, `nnUNetPredictor`, and `nnUNetPredictor.predict_from_files`.

## Refresh Guidance

Refresh this skill when any of the following change:

- `pyproject.toml` package version, dependencies, or console scripts.
- Dataset format, path-variable behavior, conversion utilities, or `dataset.json` semantics.
- Planning/preprocessing CLI flags, planner names, plans file structure, normalization, or resampling behavior.
- Training CLI/API signatures, trainer variants, checkpoint names, logging outputs, or DDP/device behavior.
- Inference/evaluation/postprocessing/model-sharing commands or `nnUNetPredictor` defaults.
- Extension discovery, custom trainer sharing rules, image I/O, normalization, or planner/preprocessor extension points.
