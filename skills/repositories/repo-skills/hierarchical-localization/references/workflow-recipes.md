# HLoc workflow recipes

Use this reference for the package-level order of operations before loading a focused sub-skill. It distills the public `hloc` workflow into reusable agent steps without requiring access to the original repository checkout.

## Canonical coarse-to-fine localization pipeline

1. **Extract local features for database and query images.** Route to `sub-skills/feature-retrieval/` for built-in extractor configs such as `superpoint_aachen`, `superpoint_inloc`, `disk`, `aliked-n16`, `sift`, or external HDF5 feature files.
2. **Build or load a reference SfM model.** Route to `sub-skills/mapping-localization/` for `reconstruction.main`, `triangulation.main`, `colmap_from_nvm`, and pycolmap/COLMAP folder contracts.
3. **Generate database image pairs for mapping.** Use covisibility pairs when an existing model is available, retrieval pairs when global descriptors are available, exhaustive pairs for small unordered sets, or pose-neighbor pairs when poses are known.
4. **Match local features for selected pairs.** Route to `feature-retrieval` for `match_features.main` or `match_dense.main`, exact match config names, and HDF5 match-file validation.
5. **Triangulate or reconstruct the reference model.** Route to `mapping-localization` for required `features`, `matches`, `pairs`, `image_dir`, `sfm_dir`, camera mode, and option-passing details.
6. **Extract global descriptors and retrieve database images for each query.** Use `extract_features.confs["netvlad"]` or another global descriptor config, then `pairs_from_retrieval.main`.
7. **Match query-to-database pairs.** Use the same local feature file and compatible match config; verify that image names in feature files, pair files, and the reference model match exactly.
8. **Localize queries.** Use `localize_sfm.main` for SfM models or `localize_inloc.main` for InLoc-style RGB-D scan datasets. Save the pose text file and log pickle.
9. **Visualize/debug only after core artifacts are valid.** Visualization helpers are optional; the primary debugging signal is the localization log with retrieved database images, matches, PnP inliers, and selected pose.

## Minimal generic SfM command skeleton

This skeleton assumes the user already has an installed `hloc` package and an image directory. Replace placeholders with user paths.

```python
from pathlib import Path
from hloc import extract_features, match_features, pairs_from_retrieval, reconstruction

images = Path("images")
outputs = Path("outputs/sfm")
outputs.mkdir(parents=True, exist_ok=True)

retrieval_conf = extract_features.confs["netvlad"]
feature_conf = extract_features.confs["superpoint_aachen"]
matcher_conf = match_features.confs["superglue"]

retrieval_path = extract_features.main(retrieval_conf, images, outputs)
sfm_pairs = outputs / "pairs-netvlad.txt"
pairs_from_retrieval.main(retrieval_path, sfm_pairs, num_matched=5)
feature_path = extract_features.main(feature_conf, images, outputs)
match_path = match_features.main(matcher_conf, sfm_pairs, feature_conf["output"], outputs)
model = reconstruction.main(outputs / "sfm_superpoint+superglue", images, sfm_pairs, feature_path, match_path)
```

For command-line equivalents and option details, load `sub-skills/feature-retrieval/` and `sub-skills/mapping-localization/`.

## Tiny demo-style mapping/localization pattern

For a small scene where a set of reference images is mapped first and one query is localized later:

1. Use `extract_features.main(feature_conf, images, image_list=references, feature_path=features)`.
2. Use exhaustive pairs for a small reference set.
3. Run `match_features.main(matcher_conf, sfm_pairs, features=features, matches=matches)`.
4. Run `reconstruction.main(sfm_dir, images, sfm_pairs, features, matches, image_list=references)`.
5. Extract query features into the same feature file with `overwrite=True` only for the query entry.
6. Generate query-to-reference pairs with an explicit query list and reference list.
7. Match query pairs with `overwrite=True` only when intentionally replacing existing pair groups.
8. Use `localize_sfm.QueryLocalizer` and `pose_from_cluster` for interactive debugging, or `localize_sfm.main` for batch localization.

This pattern can still download neural weights when built-in learned models are first used; do not treat it as an offline smoke test unless the required data and caches are present.

## Dataset-specific pipeline planning

Load `sub-skills/dataset-pipelines/` when the user names Aachen, Aachen v1.1, InLoc, 4Seasons, 7Scenes, CMU, Cambridge, RobotCar, a benchmark result file, or a dataset-specific pipeline module. Those routes involve external dataset layouts and can be network-, disk-, or runtime-heavy. Prefer safe planning and parser/help checks before any download or full run.

## Custom artifact and model interoperability

Load `sub-skills/custom-interop/` when the user has:

- External local feature HDF5 files.
- External global descriptor HDF5 files for retrieval.
- External match HDF5 files.
- A new PyTorch extractor/matcher module to integrate into `hloc`.
- Parser errors involving image lists, retrieval pairs, pair group names, or pose files.

Validate schemas and names before invoking reconstruction or localization.
