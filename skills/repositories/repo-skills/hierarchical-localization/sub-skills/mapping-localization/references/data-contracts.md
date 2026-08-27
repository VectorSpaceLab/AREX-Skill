# Data contracts for hloc mapping/localization

All names in image lists, pair files, HDF5 groups, and model images must match exactly. Avoid spaces in image names because hloc pair and list parsers split on whitespace.

## Plain image lists

Used by exhaustive pair generation, reconstruction API subset selection, and many feature/matching workflows.

```text
# blank lines and comments are accepted in image lists
reference/img001.jpg
reference/img002.jpg
reference/subdir/img003.jpg
```

Contract:

- One image name per non-empty line.
- Names are relative to the image directory passed to hloc commands.
- Blank lines and lines whose first character is `#` are ignored.
- Extra columns are ignored by the plain image-list parser; treat extra tokens as a mistake unless intentionally using an intrinsics list with the query parser.
- At least one image must be present after comments/blank lines are removed.

## Query intrinsics lists

Required by `localize_sfm`. Each query line contains an image name followed by a COLMAP/pycolmap camera model, width, height, and camera parameters.

```text
query/day/query001.jpg SIMPLE_PINHOLE 1600 1200 1200.0 800.0 600.0
query/day/query002.jpg PINHOLE 1600 1200 1180.0 1190.0 800.0 600.0
query/fisheye/query003.jpg OPENCV 1920 1080 900.0 901.0 960.0 540.0 0.01 -0.02 0.0 0.0
```

Contract:

- Non-comment line format: `name MODEL width height params...`.
- `width` and `height` are positive integers.
- `params` are numeric and must match the selected camera model's expected parameter count.
- Common parameter counts: `SIMPLE_PINHOLE=3`, `PINHOLE=4`, `SIMPLE_RADIAL=4`, `RADIAL=5`, `OPENCV=8`, `OPENCV_FISHEYE=8`, `FULL_OPENCV=12`, `FOV=5`, `SIMPLE_RADIAL_FISHEYE=4`, `RADIAL_FISHEYE=5`, `THIN_PRISM_FISHEYE=12`.

## Pair and retrieval files

The same two-column text contract is used by retrieval, pair generation, matching, reconstruction, triangulation, and localization.

```text
query/query001.jpg reference/img012.jpg
query/query001.jpg reference/img044.jpg
query/query002.jpg reference/img003.jpg
```

Contract:

- One pair per non-empty line.
- Exactly two whitespace-separated tokens per non-empty line: `name0 name1`.
- Comments are not part of the hloc pair/retrieval parser contract; keep pair files comment-free.
- Names may include `/`, but not spaces.
- For localization, the left column is the query name and the right column is a database/reference image name.
- For reconstruction/triangulation, both columns are model image names.
- Duplicate pairs are not useful; reverse duplicates may be ignored by database import but should be cleaned up for deterministic runs.

## Local feature HDF5 files

Mapping and localization need local keypoints stored under image-name groups.

```text
features.h5
└── image/name.jpg
    ├── keypoints              # required for mapping/localization
    ├── descriptors            # required by many matchers, not read by reconstruction/localization
    ├── scores                 # optional
    └── image_size             # optional
```

Contract:

- Group path equals the image name. If the image name contains `/`, HDF5 stores nested groups; hloc reads the full path transparently.
- `keypoints` is required when the command needs keypoints for that image.
- `keypoints` must be a numeric two-dimensional array with at least two columns, usually `(N, 2)` in image coordinates.
- `keypoints` may carry an `uncertainty` attribute used by model-aware triangulation verification.
- Reconstruction and triangulation require keypoints for every registered/model image in the pair file.
- `localize_sfm` requires query keypoints. It obtains database 2D/3D observations from the reference model, not from the query feature file.
- `localize_inloc` requires keypoints for both queries and retrieved database images because database keypoints are interpolated into RGB-D scan coordinates.

## Global descriptor HDF5 files

Retrieval pair generation needs global descriptors.

```text
global-feats.h5
└── image/name.jpg
    └── global_descriptor       # required by pairs_from_retrieval
```

Contract:

- `global_descriptor` is required for every query image and every database image considered by retrieval.
- Query and database descriptors may be stored in the same HDF5 file or separate files.
- Descriptor arrays for all selected images must have the same shape so they can be stacked into a score matrix.

## Match HDF5 files

Sparse match files store one group per image pair. hloc first looks for the forward pair name, then the reverse pair name, then older underscore-separated names.

For image names `name0` and `name1`, the current pair group name is:

```python
name0.replace("/", "-") + "/" + name1.replace("/", "-")
```

Example:

```text
matches.h5
└── query-query001.jpg
    └── reference-img012.jpg
        ├── matches0            # required; length = number of keypoints in first stored image
        └── matching_scores0    # required; same length as matches0
```

Contract:

- Required datasets in each pair group: `matches0` and `matching_scores0`.
- `matches0` is a one-dimensional integer array; `-1` means unmatched and non-negative values index keypoints in the second stored image.
- `matching_scores0` is a one-dimensional numeric array with the same length as `matches0`.
- If a reverse group is used, hloc flips the resulting match index pairs internally.
- A missing pair group usually means the match file was produced with a different pair file or different image names.

## COLMAP/pycolmap model folders

A binary model folder passed to hloc should contain:

```text
sfm_model/
├── cameras.bin
├── images.bin
├── points3D.bin
├── frames.bin       # present in newer model versions
└── rigs.bin         # present in newer model versions
```

Contract:

- Pair/image names must match `image.name` entries in `images.bin`.
- Covisibility pair generation and SfM localization require registered images and useful 3D points/tracks.
- Pose-neighbor pair generation requires `images.bin` camera poses.
- Reconstruction output additionally contains `database.db`, `models/`, and `colmap.LOG.*` files.
- When multiple reconstruction candidates are created, hloc moves the largest model's binary files to the requested SfM directory root.

## Pose result files

`localize_sfm` and `localize_inloc` write pose text files and pickle logs.

```text
query001.jpg qw qx qy qz tx ty tz
query002.jpg qw qx qy qz tx ty tz
```

Contract:

- One localized query pose per line.
- Quaternion order in the text file is `qw qx qy qz`.
- Translation is the `cam_from_world` translation from pycolmap.
- With `prepend_camera_name=True`, `localize_sfm` writes `parent/name.jpg` instead of only the image basename.
- Log pickle path is exactly `<results>_logs.pkl`.
- Inspect logs for `PnP_ret`, `num_inliers`, database image IDs, and query-to-3D correspondences before treating all output lines as high-confidence poses.

## NVM import files

`colmap_from_nvm` converts NVM camera/point data into a COLMAP binary model using image and camera IDs recovered from an existing COLMAP database.

Inputs:

```text
model.nvm
intrinsics.txt
database.db
```

Intrinsics line format:

```text
image/name.jpg CAMERA_MODEL width height params...
```

Contract:

- Every image name in the NVM and intrinsics files must already exist in `database.db`.
- The camera model and parameter count must be valid for COLMAP.
- `--skip_points` omits 3D points; use it only when the downstream task needs poses/cameras rather than 3D tracks.
- Output is a COLMAP binary model folder usable by hloc mapping/localization commands.
