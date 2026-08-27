# HLoc interoperability data formats

Use this reference when validating or exporting files for HLoc without relying on built-in extractors or matchers. All image names must be stable across every file: image lists, HDF5 groups, retrieval pair files, match files, SfM model image names, and query lists should use the same relative image names.

## Naming rules shared by all formats

- Image names are usually paths relative to the image root, for example `db/1.jpg`, `query/night/0001.jpg`, or `images/img0001.png`.
- Do not use spaces in image names. HLoc text parsers split on whitespace.
- Preserve case exactly. HDF5 group lookup and COLMAP image names are case-sensitive.
- Keep directory prefixes consistent. `db/1.jpg`, `./db/1.jpg`, and `1.jpg` are different names.
- For HDF5 feature groups, an image name containing `/` is stored as an HDF5 path. Accessing `fd["db/1.jpg"]` is correct.

## Local feature HDF5 files

A local feature file is an HDF5 file with one group per image name. Each leaf image group contains datasets.

Example layout:

```text
features.h5
├── db/1.jpg/
│   ├── keypoints          float32 or float16, shape (N, 2)
│   ├── descriptors        float32 or float16, shape (D, N)
│   ├── scores             float32 or float16, shape (N,)       optional but common
│   ├── scales             float32 or float16, shape (N,)       optional; needed by AdaLAM-style matchers
│   ├── oris               float32 or float16, shape (N,)       optional; needed by AdaLAM-style matchers
│   └── image_size         int or float, shape (2,) = [width, height]
└── query/q1.jpg/
    └── ...
```

Required for broad HLoc interoperability:

| Dataset | Requirement | Notes |
| --- | --- | --- |
| `keypoints` | `N x 2`, numeric | x/y coordinates in original image pixels. HLoc adds the COLMAP `+0.5` origin shift when importing to COLMAP, so do not pre-add that shift for normal HLoc use. |
| `descriptors` | `D x N`, numeric | Sparse descriptor convention is descriptor dimension by number of keypoints. `(N, D)` is a common external-export mistake. |
| `image_size` | shape `(2,)`, positive `[width, height]` | HLoc-generated files contain this field. Sparse matching code uses it to synthesize `image0`/`image1` tensors for matchers. |
| `scores` | shape `(N,)`, numeric | Required by SuperGlue-style matchers and useful for sorting/debugging. If unknown, use a constant vector only when the downstream matcher can tolerate it. |
| `scales`, `oris` | each shape `(N,)`, numeric | Needed by AdaLAM-style geometric filtering; optional otherwise. |

`keypoints` may have an optional HDF5 attribute `uncertainty`. HLoc uses this during some geometric verification paths; when absent it falls back to a default uncertainty.

A file intended only for importing keypoints into reconstruction or localization can be smaller, but any file meant to support HLoc sparse matching should include `descriptors`, `image_size`, and matcher-specific optional fields.

## Global descriptor HDF5 files

A global descriptor file is also one HDF5 group per image name. Each group contains:

| Dataset | Requirement | Notes |
| --- | --- | --- |
| `global_descriptor` | one-dimensional numeric vector `(D,)` | All images used together for retrieval must have the same descriptor length. Normalize descriptors if the retrieval model expects dot-product similarity on normalized vectors. |

Example layout:

```text
global-feats.h5
├── db/1.jpg/global_descriptor       shape (D,)
├── db/2.jpg/global_descriptor       shape (D,)
└── query/q1.jpg/global_descriptor   shape (D,)
```

HLoc retrieval pair generation reads descriptors for query and database names, stacks them into matrices, computes dot-product similarities, masks self-matches, and writes text pairs.

## Retrieval and pair text files

Retrieval and pair files are plain text with one pair per non-empty line:

```text
query/q1.jpg db/1.jpg
query/q1.jpg db/2.jpg
query/q2.jpg db/3.jpg
```

Parser behavior:

- Each line must split into exactly two whitespace-separated tokens: `query_name reference_name`.
- Repeated query names are expected; HLoc groups references by query.
- Blank lines are ignored by the retrieval parser.
- Comment lines are not part of the retrieval parser contract. Do not place `#` comments in retrieval/pair files.
- Self-pairs are usually filtered when HLoc generates retrieval pairs, but external pair files should avoid accidental self-pairs unless the downstream workflow explicitly needs them.

The same two-column format is used for sparse matching pairs, retrieval pairs, covisibility pairs, pose-neighbor pairs, and localization query-to-database candidate lists.

## Sparse match HDF5 files

A match file is an HDF5 file with one group per image pair. For a pair line:

```text
name0 name1
```

HLoc's current pair group name is:

```python
name0.replace("/", "-") + "/" + name1.replace("/", "-")
```

Because `/` is the HDF5 path separator, this creates a nested HDF5 path. For example:

```text
name0 = "query/q1.jpg"
name1 = "db/1.jpg"
current pair path = "query-q1.jpg/db-1.jpg"
```

HLoc readers also check the reversed order and a legacy underscore separator:

```python
name0.replace("/", "-") + "_" + name1.replace("/", "-")
```

Prefer writing the current slash-separated pair path for new files. The reader lookup order is current forward, current reverse, legacy forward, legacy reverse. If only the reverse pair exists, HLoc flips the returned `(idx0, idx1)` match pairs.

Each final sparse match group should contain:

| Dataset | Requirement | Notes |
| --- | --- | --- |
| `matches0` | integer array shape `(N0,)` | For each keypoint index in image0, stores the matching keypoint index in image1, or `-1` if unmatched. |
| `matching_scores0` | numeric array shape `(N0,)` | Confidence per image0 keypoint. Downstream readers expect this dataset. Use `0` for unmatched entries if no confidence exists. |

Validation against feature files:

- `len(matches0)` should equal the number of keypoints in `name0`.
- Every non-negative `matches0[i]` should be `<` the number of keypoints in `name1`.
- `matching_scores0` should have the same length as `matches0`.

Dense matching may create intermediate datasets such as `keypoints0`, `keypoints1`, and `scores` before assignment to sparse keypoint indices. For interoperability with reconstruction/localization, ensure the final file has `matches0` and `matching_scores0`.

## Image list files

Plain image list:

```text
# comments and blank lines are allowed here
db/1.jpg
db/2.jpg
query/q1.jpg
```

Parser behavior for plain lists:

- Blank lines and lines starting with `#` are skipped.
- The first whitespace-separated token is the image name.
- Avoid extra columns in a plain list because they can hide mistakes when a downstream command expected an intrinsics list.

Query image list with camera intrinsics:

```text
query/q1.jpg SIMPLE_PINHOLE 640 480 500 320 240
query/q2.jpg PINHOLE 640 480 510 509 321 239
```

Format:

```text
image_name CAMERA_MODEL width height params...
```

Common camera parameter counts:

| Camera model | Parameter order |
| --- | --- |
| `SIMPLE_PINHOLE` | `f cx cy` |
| `PINHOLE` | `fx fy cx cy` |
| `SIMPLE_RADIAL` | `f cx cy k` |
| `RADIAL` | `f cx cy k1 k2` |
| `OPENCV` | `fx fy cx cy k1 k2 p1 p2` |
| `OPENCV_FISHEYE` | `fx fy cx cy k1 k2 k3 k4` |
| `FULL_OPENCV` | `fx fy cx cy k1 k2 p1 p2 k3 k4 k5 k6` |
| `SIMPLE_RADIAL_FISHEYE` | `f cx cy k` |
| `RADIAL_FISHEYE` | `f cx cy k1 k2` |
| `THIN_PRISM_FISHEYE` | `fx fy cx cy k1 k2 p1 p2 k3 k4 sx1 sy1` |

HLoc constructs a `pycolmap.Camera` from these fields when localizing SfM queries. Width and height must be positive integers, and camera parameters must be floats.

## Pose result files

HLoc pose writers produce one line per localized query:

```text
image_name qw qx qy qz tx ty tz
```

Notes:

- Quaternion order is `qw qx qy qz`.
- Translation follows as `tx ty tz`.
- The pose is the camera-from-world transform returned by localization.
- With camera-name prepending enabled, the output name can keep one parent directory component; otherwise the basename is used by the writer.

## Validation command examples

Create tiny example files:

```bash
python sub-skills/custom-interop/scripts/validate_hloc_formats.py --create-example hloc-format-example
```

Validate a feature file and retrieval pairs:

```bash
python sub-skills/custom-interop/scripts/validate_hloc_formats.py \
  --features outputs/features.h5 \
  --retrieval pairs-query-db.txt
```

Validate matches against both feature keypoint counts and retrieval pairs:

```bash
python sub-skills/custom-interop/scripts/validate_hloc_formats.py \
  --features outputs/features.h5 \
  --matches outputs/matches.h5 \
  --retrieval pairs-query-db.txt \
  --strict
```
