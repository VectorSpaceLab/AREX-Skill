---
name: hierarchical-localization
description: "Use the hloc Hierarchical-Localization toolbox for visual
  localization, feature retrieval, matching, SfM mapping, dataset pipelines, and
  custom HDF5 interoperability."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Hierarchical-Localization (hloc)

Use this repo skill when a task involves the `hloc` visual localization toolbox: 6-DoF image localization, image retrieval pairs, local feature extraction, SuperPoint/SuperGlue/LightGlue/LoFTR workflows, pycolmap/COLMAP SfM models, Aachen or InLoc pipelines, or HDF5 feature/match interoperability.

## Install and import check

`hloc` is a Python package whose distribution name and import name are both `hloc`. It requires Python, PyTorch/torchvision, OpenCV, NumPy/SciPy/HDF5 tooling, `pycolmap`, `kornia`, and other runtime dependencies. Learned extractors and matchers can download model weights on first use; CUDA accelerates many models but is not required for parser/import/data-format checks.

Minimal check in the user's active environment:

```bash
python -c "import hloc; print(hloc.__version__)"
python -m hloc.extract_features --help
python -m hloc.reconstruction --help
```

For a fuller safe diagnostic, run the bundled helper:

```bash
python scripts/check_hloc_environment.py --check-cli
```

## Route by task

- Load [feature-retrieval](sub-skills/feature-retrieval/SKILL.md) for built-in local/global feature extraction, NetVLAD-style retrieval descriptors, sparse/dense matching, exact config names, output file naming, and feature/match HDF5 schemas.
- Load [mapping-localization](sub-skills/mapping-localization/SKILL.md) for pair generation, reconstruction, triangulation, COLMAP/pycolmap model folders, `localize_sfm`, `localize_inloc`, query pose outputs, and localization logs.
- Load [dataset-pipelines](sub-skills/dataset-pipelines/SKILL.md) for Aachen, Aachen v1.1, InLoc, SfM demo, 4Seasons, 7Scenes, CMU, Cambridge, or RobotCar planning. These workflows usually require external datasets and should not be launched as routine smoke tests.
- Load [custom-interop](sub-skills/custom-interop/SKILL.md) for external feature/global-descriptor/match HDF5 files, new extractor or matcher modules, `BaseModel`/`dynamic_load`, list/pair/pose schemas, and custom artifact validation.

## Canonical workflow shape

Most HLoc tasks combine multiple routes:

1. Choose feature/retrieval/matcher configs and produce feature or descriptor HDF5 files (`feature-retrieval`).
2. Generate database or query pairs from retrieval, covisibility, poses, or exhaustive combinations (`mapping-localization`).
3. Match selected image pairs and validate HDF5 pair groups (`feature-retrieval` plus `mapping-localization`).
4. Reconstruct or triangulate a reference SfM model with pycolmap (`mapping-localization`).
5. Retrieve and match database images for each query (`feature-retrieval`).
6. Localize query images and inspect pose/log outputs (`mapping-localization`).
7. When the request names a public benchmark dataset, first read `dataset-pipelines` to verify the dataset layout and skip network/benchmark-scale surprises.

Read [references/workflow-recipes.md](references/workflow-recipes.md) for cross-sub-skill pipeline recipes before composing a long command sequence.

## Public runtime references and helpers

- [references/repo-provenance.md](references/repo-provenance.md) records the source commit, package version, evidence paths, and refresh baseline.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) contains structured managed-router metadata for this skill.
- [references/workflow-recipes.md](references/workflow-recipes.md) summarizes generic SfM/localization, tiny demo-style, dataset, and custom-interoperability flows.
- [references/troubleshooting.md](references/troubleshooting.md) covers install/import, model-download, CPU/GPU, pycolmap, artifact naming, and dataset-scale safety issues shared by multiple routes.
- [scripts/check_hloc_environment.py](scripts/check_hloc_environment.py) checks installed `hloc` imports, versions, configs, optional CUDA status, and safe CLI parsers without running model inference or downloading data.

## Safety and boundary rules

- Do not treat full Aachen/InLoc/RobotCar/CMU/4Seasons/Cambridge/7Scenes runs as safe smoke tests; they require external datasets, large outputs, and often model downloads.
- Do not assume CUDA is required. Verify the user's goal: CUDA is usually for speed, while CPU can validate imports, parsers, schemas, and many small logic checks.
- Keep image names consistent across lists, HDF5 groups, pair files, SfM model images, retrieval files, and pose outputs. Name mismatches are the most common cross-workflow failure.
- Prefer bundled validators and references from this skill over reopening a source checkout. If public APIs or configuration names differ from the provenance snapshot, run `refresh-repo-skill`.
