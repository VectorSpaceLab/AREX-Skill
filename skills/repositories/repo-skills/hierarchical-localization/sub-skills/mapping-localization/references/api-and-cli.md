# API and CLI reference

This reference distills the installed public hloc module signatures and their command-line flags for mapping/localization work. It is intentionally limited to runtime calls; do not depend on source checkouts or notebooks.

## Pair generators

### `hloc.pairs_from_exhaustive`

API:

```python
pairs_from_exhaustive.main(
    output,
    image_list=None,
    features=None,
    ref_list=None,
    ref_features=None,
)
```

CLI:

```bash
python -m hloc.pairs_from_exhaustive \
  --output pairs.txt \
  [--image_list image_list.txt | --features features.h5] \
  [--ref_list ref_list.txt | --ref_features ref_features.h5]
```

Contract:

- Provide `image_list` or `features` for query names.
- If no reference list/features is provided, it self-matches query names once and skips identical/repeated pairs.
- If a reference list/features is provided, it emits all query-reference pairs.

### `hloc.pairs_from_retrieval`

API:

```python
pairs_from_retrieval.main(
    descriptors,
    output,
    num_matched,
    query_prefix=None,
    query_list=None,
    db_prefix=None,
    db_list=None,
    db_model=None,
    db_descriptors=None,
)
```

CLI:

```bash
python -m hloc.pairs_from_retrieval \
  --descriptors global-feats.h5 \
  --output pairs-retrieval.txt \
  --num_matched 20 \
  [--query_prefix prefix ...] \
  [--query_list queries.txt] \
  [--db_prefix prefix ...] \
  [--db_list database_images.txt] \
  [--db_model sfm_model] \
  [--db_descriptors database-global-feats.h5]
```

Contract:

- `descriptors` must be an HDF5 file with per-image `global_descriptor` datasets for queries.
- `db_descriptors` may point to a separate database descriptor file; otherwise the same descriptor file is used for queries and database images.
- `query_prefix`/`db_prefix` accept one or more prefixes. Use either prefix filters or explicit lists, not both for the same side.
- `db_model` restricts database names to images registered in a COLMAP model.
- Self-matches are masked out; scores below zero are rejected by the retrieval helper.

### `hloc.pairs_from_covisibility`

API:

```python
pairs_from_covisibility.main(model, output, num_matched)
```

CLI:

```bash
python -m hloc.pairs_from_covisibility \
  --model sfm_model \
  --output pairs-covisibility.txt \
  --num_matched 20
```

Contract:

- `model` is a COLMAP/pycolmap model folder.
- The model must contain registered images and 3D points/tracks.
- For each image, the output pairs are the top covisible images by shared 3D-point count.

### `hloc.pairs_from_poses`

API:

```python
pairs_from_poses.main(model, output, num_matched, rotation_threshold=30)
```

CLI:

```bash
python -m hloc.pairs_from_poses \
  --model posed_model \
  --output pairs-poses.txt \
  --num_matched 20 \
  [--rotation_threshold 30]
```

Contract:

- `model` must contain `images.bin` with camera poses.
- Pair scores are negative camera-center distances.
- Pairs whose camera principal axes differ by at least `rotation_threshold` degrees are invalidated.

## Reconstruction

API:

```python
reconstruction.main(
    sfm_dir,
    image_dir,
    pairs,
    features,
    matches,
    camera_mode=pycolmap.CameraMode.AUTO,
    verbose=False,
    skip_geometric_verification=False,
    min_match_score=None,
    image_list=None,
    image_options=None,
    mapper_options=None,
)
```

CLI:

```bash
python -m hloc.reconstruction \
  --sfm_dir outputs/sfm \
  --image_dir images \
  --pairs pairs.txt \
  --features features.h5 \
  --matches matches.h5 \
  [--camera_mode AUTO|SINGLE|PER_FOLDER|PER_IMAGE] \
  [--skip_geometric_verification] \
  [--min_match_score 0.2] \
  [--verbose] \
  [--image_options key=value ...] \
  [--mapper_options key=value ...]
```

Contract:

- `features`, `pairs`, and `matches` must already exist.
- `image_dir` must contain the images referenced by the model import step; use `image_list` through the API when only a subset should be imported.
- `image_options` are validated against `pycolmap.ImageReaderOptions`.
- `mapper_options` are validated against `pycolmap.IncrementalMapperOptions`.
- Option values are parsed as Python literals and must have the same type as the corresponding pycolmap default.
- Returns the largest `pycolmap.Reconstruction` or `None` if no model is reconstructed.

## Triangulation

API:

```python
triangulation.main(
    sfm_dir,
    reference_model,
    image_dir,
    pairs,
    features,
    matches,
    skip_geometric_verification=False,
    estimate_two_view_geometries=False,
    min_match_score=None,
    verbose=False,
    mapper_options=None,
)
```

CLI:

```bash
python -m hloc.triangulation \
  --sfm_dir outputs/triangulated \
  --reference_sfm_model posed_model \
  --image_dir images \
  --pairs pairs.txt \
  --features features.h5 \
  --matches matches.h5 \
  [--skip_geometric_verification] \
  [--min_match_score 0.2] \
  [--verbose]
```

Contract:

- `reference_model` / `--reference_sfm_model` is a COLMAP/pycolmap model folder with cameras and registered images.
- Image names in `pairs` and HDF5 files must match the reference model image names.
- When `skip_geometric_verification=False`, triangulation either estimates two-view geometry or performs model-aware geometric verification before `pycolmap.triangulate_points`.
- The Python API exposes `estimate_two_view_geometries` and `mapper_options`. Prefer the API if those are needed.

## SfM localization

### `localize_sfm.QueryLocalizer`

API:

```python
localize_sfm.QueryLocalizer(reconstruction, config=None)
```

The localizer wraps a `pycolmap.Reconstruction` and passes `config["estimation"]` and `config["refinement"]` to `pycolmap.estimate_and_refine_absolute_pose`.

### `localize_sfm.pose_from_cluster`

API:

```python
localize_sfm.pose_from_cluster(
    localizer,
    qname,
    query_camera,
    db_ids,
    features_path,
    matches_path,
    **kwargs,
)
```

This helper gathers query keypoints, query-to-database matches, visible 3D point IDs, and returns `(ret, log)` for one candidate reference cluster.

### `localize_sfm.main`

API:

```python
localize_sfm.main(
    reference_sfm,
    queries,
    retrieval,
    features,
    matches,
    results,
    ransac_thresh=12,
    covisibility_clustering=False,
    prepend_camera_name=False,
    config=None,
)
```

CLI:

```bash
python -m hloc.localize_sfm \
  --reference_sfm sfm_model \
  --queries queries_with_intrinsics.txt \
  --features query-features.h5 \
  --matches query-matches.h5 \
  --retrieval pairs-query-db.txt \
  --results query_poses.txt \
  [--ransac_thresh 12] \
  [--covisibility_clustering] \
  [--prepend_camera_name]
```

Contract:

- `queries` is an image list with intrinsics, not a plain image list.
- `retrieval` maps query names to reference model image names.
- `features` must contain `keypoints` for query names.
- `matches` must contain query-reference pair groups for the retrieval file.
- `results` is a text pose file; a pickle log is also written at `<results>_logs.pkl`.
- If `covisibility_clustering=True`, retrieved database images are split into connected components in the reference model and the best cluster by inlier count is selected.

## InLoc-style localization

API:

```python
localize_inloc.main(
    dataset_dir,
    retrieval,
    features,
    matches,
    results,
    skip_matches=None,
)
```

CLI:

```bash
python -m hloc.localize_inloc \
  --dataset_dir dataset \
  --retrieval inloc-retrieval.txt \
  --features inloc-features.h5 \
  --matches inloc-matches.h5 \
  --results inloc_poses.txt \
  [--skip_matches 20]
```

Contract:

- `retrieval` maps each query image path to retrieved database image paths.
- `features` must contain `keypoints` for both query and retrieved database image names.
- `matches` must contain pair groups for the retrieval file.
- For every retrieved database image `r`, `dataset_dir / (r + ".mat")` must contain an `XYZcut` scan array.
- The scan alignment transform is looked up from the dataset tree using floor, scan, and building names embedded in `r`.

## NVM import

API:

```python
colmap_from_nvm.main(nvm, intrinsics, database, output, skip_points=False)
```

CLI:

```bash
python -m hloc.colmap_from_nvm \
  --nvm model.nvm \
  --intrinsics intrinsics.txt \
  --database database.db \
  --output colmap_model \
  [--skip_points]
```

Contract:

- `database` must already contain rows for the image names in the NVM and intrinsics files.
- `intrinsics` uses one line per image: `name camera_model width height params...`.
- Camera model names and parameter counts must be valid COLMAP camera model definitions.
- Output is a COLMAP binary model folder.

## Shared helpers

```python
triangulation.parse_option_args(args, default_options) -> dict
```

Parses `key=value` option lists for pycolmap options. It raises when a key is unknown or a value has the wrong type.

```python
parsers.parse_image_lists(paths, with_intrinsics=False)
parsers.parse_retrieval(path)
parsers.names_to_pair(name0, name1, separator="/")
io.write_poses(poses, path, prepend_camera_name)
```

These define the image-list, pair/retrieval, match-group, and pose-output contracts summarized in [data-contracts.md](data-contracts.md).
