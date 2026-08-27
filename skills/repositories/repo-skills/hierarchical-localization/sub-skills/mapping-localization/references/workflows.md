# Mapping and localization workflows

These recipes assume that feature extraction and matching have already produced hloc-compatible HDF5 files. For built-in extractor/matcher configuration choices, route to `../feature-retrieval/`. Use paths below as placeholders and replace them with project-local paths.

## Common artifact layout

```text
images/                         # input images, names match list/pair files
outputs/features.h5             # local keypoints; global descriptors only when retrieval pairs are generated
outputs/matches.h5              # hloc match groups for the selected pairs
outputs/pairs-exhaustive.txt     # or pairs-retrieval.txt / pairs-covisibility.txt / pairs-poses.txt
outputs/sfm/                    # COLMAP/pycolmap model and database outputs
outputs/query_poses.txt         # localization poses
outputs/query_poses.txt_logs.pkl
```

Always validate file names and HDF5 keys before expensive pycolmap calls:

```bash
python sub-skills/mapping-localization/scripts/validate_hloc_inputs.py \
  --workflow reconstruction \
  --image-list image_list.txt \
  --pairs outputs/pairs.txt \
  --features outputs/features.h5 \
  --matches outputs/matches.h5 \
  --image-dir images
```

## 1. Pair generation

### Exhaustive pairs

Use exhaustive pairs for small image sets or when retrieval quality is unknown. It emits each self-matching pair once and skips same-image pairs.

```bash
python -m hloc.pairs_from_exhaustive \
  --image_list image_list.txt \
  --output outputs/pairs-exhaustive.txt
```

Alternative inputs:

```bash
python -m hloc.pairs_from_exhaustive \
  --features outputs/features.h5 \
  --output outputs/pairs-exhaustive.txt
```

For query-vs-reference exhaustive matching, provide separate query/reference lists or feature files:

```bash
python -m hloc.pairs_from_exhaustive \
  --image_list queries.txt \
  --ref_list references.txt \
  --output outputs/pairs-query-db.txt
```

Python API skeleton:

```python
from pathlib import Path
from hloc import pairs_from_exhaustive

pairs_from_exhaustive.main(
    output=Path("outputs/pairs-exhaustive.txt"),
    image_list=Path("image_list.txt"),
)
```

### Retrieval pairs from global descriptors

Use retrieval pairs when a global descriptor HDF5 file contains `global_descriptor` for each candidate image.

```bash
python -m hloc.pairs_from_retrieval \
  --descriptors outputs/global-feats.h5 \
  --output outputs/pairs-retrieval.txt \
  --num_matched 20
```

Restrict query/reference sets when the same descriptor file contains multiple subsets:

```bash
python -m hloc.pairs_from_retrieval \
  --descriptors outputs/global-feats.h5 \
  --query_list queries.txt \
  --db_list database_images.txt \
  --output outputs/pairs-query-db.txt \
  --num_matched 30
```

Use `--query_prefix` and `--db_prefix` only when image names have stable prefixes. Use `--db_model sfm_model` to restrict database candidates to images registered in a reference model. Use `--db_descriptors` when database descriptors are in a separate HDF5 file.

Python API skeleton:

```python
from pathlib import Path
from hloc import pairs_from_retrieval

pairs_from_retrieval.main(
    descriptors=Path("outputs/global-feats.h5"),
    output=Path("outputs/pairs-retrieval.txt"),
    num_matched=20,
    query_list=Path("queries.txt"),
    db_list=Path("database_images.txt"),
)
```

### Covisibility pairs from an existing model

Use covisibility pairs when a COLMAP/pycolmap model already has registered images and 3D tracks. Each image is paired with the top `num_matched` images that share the most 3D points.

```bash
python -m hloc.pairs_from_covisibility \
  --model sfm_model \
  --output outputs/pairs-covisibility.txt \
  --num_matched 20
```

Python API skeleton:

```python
from pathlib import Path
from hloc import pairs_from_covisibility

pairs_from_covisibility.main(
    model=Path("sfm_model"),
    output=Path("outputs/pairs-covisibility.txt"),
    num_matched=20,
)
```

### Pose-neighbor pairs from known camera poses

Use pose-neighbor pairs when the reference model has camera poses and nearby-view matching is preferred. Pairs are selected by camera-center distance while rejecting cameras whose principal axes differ by at least `rotation_threshold` degrees.

```bash
python -m hloc.pairs_from_poses \
  --model posed_model \
  --output outputs/pairs-poses.txt \
  --num_matched 20 \
  --rotation_threshold 30
```

Python API skeleton:

```python
from pathlib import Path
from hloc import pairs_from_poses

pairs_from_poses.main(
    model=Path("posed_model"),
    output=Path("outputs/pairs-poses.txt"),
    num_matched=20,
    rotation_threshold=30,
)
```

## 2. Sparse reconstruction from images, features, and matches

Use reconstruction to build a new sparse model from an image directory, pair file, local feature HDF5, and match HDF5. The command creates a COLMAP database, imports images/keypoints/matches, optionally verifies geometry, runs pycolmap incremental mapping, and moves the largest model to the output SfM directory.

```bash
python -m hloc.reconstruction \
  --sfm_dir outputs/sfm \
  --image_dir images \
  --pairs outputs/pairs.txt \
  --features outputs/features.h5 \
  --matches outputs/matches.h5 \
  --camera_mode AUTO
```

Useful options:

```bash
python -m hloc.reconstruction \
  --sfm_dir outputs/sfm \
  --image_dir images \
  --pairs outputs/pairs.txt \
  --features outputs/features.h5 \
  --matches outputs/matches.h5 \
  --camera_mode SINGLE \
  --image_options camera_model='"PINHOLE"' \
  --mapper_options min_num_matches=15 ba_refine_focal_length=True \
  --min_match_score 0.2 \
  --verbose
```

Option values are parsed as Python literals and must match the underlying pycolmap option type. Strings therefore need shell-safe quotes as shown above.

Python API skeleton:

```python
from pathlib import Path
import pycolmap
from hloc import reconstruction

model = reconstruction.main(
    sfm_dir=Path("outputs/sfm"),
    image_dir=Path("images"),
    pairs=Path("outputs/pairs.txt"),
    features=Path("outputs/features.h5"),
    matches=Path("outputs/matches.h5"),
    camera_mode=pycolmap.CameraMode.AUTO,
    verbose=False,
    skip_geometric_verification=False,
    min_match_score=None,
    image_list=None,
    image_options={"camera_model": "PINHOLE"},
    mapper_options={"min_num_matches": 15},
)
```

Expected outputs in `outputs/sfm/`:

- `database.db` with imported images, keypoints, matches, and two-view geometry.
- `cameras.bin`, `images.bin`, `points3D.bin`, plus `frames.bin` and `rigs.bin` when present in the pycolmap/COLMAP model.
- `models/` containing pycolmap reconstruction candidates.
- `colmap.LOG.*` files.

## 3. Triangulation from known camera poses

Use triangulation when camera poses are already known and the task is to build or update 3D points using matched local features. The reference model must contain cameras and registered images whose names match the pair/match files.

```bash
python -m hloc.triangulation \
  --sfm_dir outputs/triangulated \
  --reference_sfm_model posed_model \
  --image_dir images \
  --pairs outputs/pairs-poses.txt \
  --features outputs/features.h5 \
  --matches outputs/matches.h5
```

Optional flags:

```bash
python -m hloc.triangulation \
  --sfm_dir outputs/triangulated \
  --reference_sfm_model posed_model \
  --image_dir images \
  --pairs outputs/pairs-poses.txt \
  --features outputs/features.h5 \
  --matches outputs/matches.h5 \
  --min_match_score 0.2 \
  --skip_geometric_verification \
  --verbose
```

Prefer the Python API when passing mapper options or when a CLI version does not expose all API options:

```python
from pathlib import Path
from hloc import triangulation

model = triangulation.main(
    sfm_dir=Path("outputs/triangulated"),
    reference_model=Path("posed_model"),
    image_dir=Path("images"),
    pairs=Path("outputs/pairs-poses.txt"),
    features=Path("outputs/features.h5"),
    matches=Path("outputs/matches.h5"),
    skip_geometric_verification=False,
    estimate_two_view_geometries=False,
    min_match_score=None,
    verbose=False,
    mapper_options={"min_num_matches": 15},
)
```

## 4. Query localization against an SfM model

Use SfM localization when a reference model is already reconstructed/triangulated and query images have known intrinsics. Inputs are:

- Reference model folder.
- Query intrinsics list.
- Retrieval file mapping each query to database/reference image names.
- Query local feature HDF5.
- Query-vs-database match HDF5.
- Output pose text path.

```bash
python -m hloc.localize_sfm \
  --reference_sfm outputs/sfm \
  --queries queries_with_intrinsics.txt \
  --retrieval outputs/pairs-query-db.txt \
  --features outputs/query-features.h5 \
  --matches outputs/query-matches.h5 \
  --results outputs/query_poses.txt \
  --ransac_thresh 12
```

Use covisibility clustering when retrieved database images may span disconnected scene components:

```bash
python -m hloc.localize_sfm \
  --reference_sfm outputs/sfm \
  --queries queries_with_intrinsics.txt \
  --retrieval outputs/pairs-query-db.txt \
  --features outputs/query-features.h5 \
  --matches outputs/query-matches.h5 \
  --results outputs/query_poses.txt \
  --covisibility_clustering \
  --prepend_camera_name
```

Python API skeleton:

```python
from pathlib import Path
from hloc import localize_sfm

localize_sfm.main(
    reference_sfm=Path("outputs/sfm"),
    queries=Path("queries_with_intrinsics.txt"),
    retrieval=Path("outputs/pairs-query-db.txt"),
    features=Path("outputs/query-features.h5"),
    matches=Path("outputs/query-matches.h5"),
    results=Path("outputs/query_poses.txt"),
    ransac_thresh=12,
    covisibility_clustering=True,
    prepend_camera_name=False,
    config={"estimation": {"ransac": {"max_error": 12}}},
)
```

`localize_sfm` writes `outputs/query_poses.txt` and `outputs/query_poses.txt_logs.pkl`. If localization fails for a query without covisibility clustering, the closest retrieved reference pose may be written as a fallback; inspect the logs and inlier counts before treating every line as a successful PnP result.

## 5. InLoc-style RGB-D scan localization

Use InLoc-style localization only when the dataset tree contains query images, database images, scan `.mat` files, and scan alignment transforms with names matching the retrieval file. Dataset-specific download/layout planning belongs in `../dataset-pipelines/`; this recipe covers only the low-level localizer call.

```bash
python -m hloc.localize_inloc \
  --dataset_dir dataset \
  --retrieval outputs/inloc-retrieval.txt \
  --features outputs/inloc-features.h5 \
  --matches outputs/inloc-matches.h5 \
  --results outputs/inloc_poses.txt \
  --skip_matches 20
```

Python API skeleton:

```python
from pathlib import Path
from hloc import localize_inloc

localize_inloc.main(
    dataset_dir=Path("dataset"),
    retrieval=Path("outputs/inloc-retrieval.txt"),
    features=Path("outputs/inloc-features.h5"),
    matches=Path("outputs/inloc-matches.h5"),
    results=Path("outputs/inloc_poses.txt"),
    skip_matches=20,
)
```

`localize_inloc` builds 2D-3D correspondences by interpolating 3D scan points at matched database keypoints, estimates an absolute pose, then writes the same pose text plus log pickle pattern as SfM localization.

## 6. NVM import overview

Use NVM import when an existing VisualSfM/NVM model must become a COLMAP binary model that hloc/pycolmap can read. The import needs a COLMAP database so image and camera IDs match existing database rows.

```bash
python -m hloc.colmap_from_nvm \
  --nvm model.nvm \
  --intrinsics intrinsics.txt \
  --database outputs/sfm/database.db \
  --output outputs/nvm_colmap_model
```

Skip points only when camera poses are needed and 3D tracks are intentionally omitted:

```bash
python -m hloc.colmap_from_nvm \
  --nvm model.nvm \
  --intrinsics intrinsics.txt \
  --database outputs/sfm/database.db \
  --output outputs/nvm_colmap_model \
  --skip_points
```

The intrinsics file uses one line per image:

```text
image/name.jpg PINHOLE 1600 1200 1200.0 1210.0 800.0 600.0
```

The output folder contains COLMAP binary model files that can be passed as `reference_sfm`, `reference_sfm_model`, or `model` depending on the downstream hloc function.
