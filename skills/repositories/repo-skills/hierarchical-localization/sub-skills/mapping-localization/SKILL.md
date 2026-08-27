---
name: mapping-localization
description: "Operate hloc pair generation, COLMAP/pycolmap mapping,
  triangulation, SfM localization, InLoc localization, and pose outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# mapping-localization

Use this sub-skill when the task is to turn prepared hloc features, retrieval descriptors, matches, image lists, and/or existing camera poses into image pairs, COLMAP/pycolmap sparse models, triangulated reference models, or query poses.

## Route here for

- Pair files from exhaustive image sets, retrieval descriptors, covisibility, or known poses.
- `hloc.reconstruction.main` / `python -m hloc.reconstruction` sparse reconstruction.
- `hloc.triangulation.main` / `python -m hloc.triangulation` triangulation from known camera poses.
- `hloc.localize_sfm.main` / `python -m hloc.localize_sfm` query localization against a COLMAP/pycolmap SfM model.
- `hloc.localize_inloc.main` / `python -m hloc.localize_inloc` InLoc-style RGB-D scan localization.
- NVM-to-COLMAP import planning with `python -m hloc.colmap_from_nvm`.

## Route away

- Feature extractor, global descriptor, dense matcher, sparse matcher, or built-in config selection details: use `../feature-retrieval/`.
- Benchmark-specific directory/download/submission layouts such as Aachen, 4Seasons, RobotCar, or complete InLoc dataset setup: use `../dataset-pipelines/`.
- Creating custom extractors/matchers or external HDF5 feature/match exports: use `../custom-interop/`.

## Required operating contract

Before running mapping or localization, identify these artifacts explicitly:

1. Image root and any image/query list files.
2. Pair or retrieval file, with exactly two whitespace-separated image names per line.
3. HDF5 local features and HDF5 matches with hloc-compatible group/dataset names.
4. For reconstruction: output SfM directory, image directory, feature file, match file, and pair file.
5. For triangulation/localization: a reference COLMAP/pycolmap model directory with binary model files.
6. For query localization: query intrinsics list and output pose path.
7. For InLoc-style localization: retrieval pairs, query/database feature and match files, and scan/alignment files in the dataset tree.

Run the bundled validator when accepting user-supplied paths or text files:

```bash
python sub-skills/mapping-localization/scripts/validate_hloc_inputs.py \
  --workflow localize-sfm \
  --query-list queries_with_intrinsics.txt \
  --pairs retrieval.txt \
  --features features.h5 \
  --matches matches.h5 \
  --reference-model sfm_model
```

## References

- [Workflow recipes](references/workflows.md)
- [API and CLI reference](references/api-and-cli.md)
- [Data contracts](references/data-contracts.md)
- [Troubleshooting](references/troubleshooting.md)
- [Input validator](scripts/validate_hloc_inputs.py)
