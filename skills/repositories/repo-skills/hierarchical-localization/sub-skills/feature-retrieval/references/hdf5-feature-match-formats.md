# HDF5 Feature, Retrieval, and Match Formats

hloc stores features and matches in HDF5 files keyed by image names and pair names. The exact strings matter: image names must match the relative names used in image lists, pair files, COLMAP models, reconstruction, triangulation, and localization.

## Image-name convention

- An image name is the POSIX-style path relative to the image root, for example `db/000001.jpg` or `query/night/001.png`.
- Do not use absolute image paths inside HDF5 group names or pair files.
- `ImageDataset` writes the same relative names it discovers or reads from `image_list`.
- If a relative name contains `/`, HDF5 displays it as nested groups. This is normal: a dataset under image name `db/000001.jpg` may appear as group `db` containing group `000001.jpg`.

Quick image-name listing:

```python
from pathlib import Path
from hloc.utils.io import list_h5_names

print(sorted(list_h5_names(Path("outputs/feats-superpoint-n4096-r1024.h5"))))
```

## Local feature HDF5 layout

Feature extraction creates one group per image name.

```text
features.h5
└── <image_name>/
    ├── keypoints          # shape (N, 2), keypoint coordinates in original image pixels
    ├── descriptors        # usually shape (D, N), descriptor per keypoint
    ├── scores             # usually shape (N,), optional but common
    ├── image_size         # shape (2,), original image size as (width, height)
    ├── scales             # optional, shape (N,)
    └── oris               # optional, shape (N,)
```

Important details:

- `keypoints` are rescaled back to the original image resolution after preprocessing. They are not coordinates in the resized tensor unless a custom exporter wrote them that way.
- `keypoints` have an HDF5 attribute `uncertainty` when the extractor exposes detection noise. `hloc.utils.io.get_keypoints(path, name, return_uncertainty=True)` returns both keypoints and this attribute.
- API extraction defaults to `as_half=True`, converting `float32` outputs to `float16`. This commonly affects `keypoints`, `descriptors`, `scores`, and similar floating datasets. Pass `as_half=False` when exact float32 storage is needed.
- Sparse matchers load all feature datasets for a pair and append `0` or `1` to each key in the data dictionary, e.g. `keypoints0`, `descriptors0`, `image_size0`.
- `AdaLAM` requires more fields than basic matchers: it needs images, descriptors, keypoints, scales, and orientations for both images. Do not choose it for feature files lacking `scales`/`oris`.

Minimal schema check:

```python
import h5py

with h5py.File("outputs/feats-superpoint-n4096-r1024.h5", "r") as f:
    name = "db/000001.jpg"
    g = f[name]
    assert "keypoints" in g and "descriptors" in g and "image_size" in g
    assert g["keypoints"].shape[-1] == 2
```

## Global retrieval descriptor HDF5 layout

Global descriptor extraction uses the same one-group-per-image convention but writes `global_descriptor` instead of local keypoint fields.

```text
global-feats-netvlad.h5
└── <image_name>/
    └── global_descriptor  # shape (D,) or equivalent one-vector descriptor
```

`pairs_from_retrieval.main` expects this dataset name exactly. It reads query descriptors from `descriptors` and database descriptors from `db_descriptors` when provided, otherwise from the same file.

```python
from pathlib import Path
from hloc import pairs_from_retrieval

pairs_from_retrieval.main(
    descriptors=Path("outputs/global-feats-netvlad.h5"),
    output=Path("outputs/pairs-netvlad.txt"),
    num_matched=20,
)
```

The output pairs text file has one query-reference pair per line:

```text
query/0001.jpg db/0100.jpg
query/0001.jpg db/0042.jpg
```

Filtering options:

- `query_prefix` / `db_prefix`: keep descriptor names beginning with those prefixes.
- `query_list` / `db_list`: keep explicit image-list entries.
- `db_model`: use database image names from a COLMAP model's `images.bin`.
- `db_descriptors`: use one or more separate descriptor HDF5 files for database images.

Retrieval avoids self-matches and keeps top dot-product scores with non-negative score after filtering.

## Pair-name convention in match HDF5 files

Sparse and dense match files are keyed by pair names derived from the pair file. Current hloc writing uses:

```python
from hloc.utils.parsers import names_to_pair
pair_key = names_to_pair(name0, name1)  # separator='/' by default
```

The rule is:

```text
pair_key = name0.replace('/', '-') + '/' + name1.replace('/', '-')
```

Example:

```text
name0 = "query/night/001.jpg"
name1 = "db/000010.jpg"
pair_key = "query-night-001.jpg/db-000010.jpg"
```

Because `/` is also the HDF5 path separator, this appears as nested groups. When manually inspecting an HDF5 file, use the full pair path. Older hloc match files may use an underscore separator:

```text
query-night-001.jpg_db-000010.jpg
```

hloc's match reader checks current forward/reverse pair names and the older underscore names in both directions. Manual validators must account for both if they read legacy files.

## Sparse match HDF5 layout

Sparse `match_features.main` creates one group per pair key.

```text
matches.h5
└── <pair_key>/
    ├── matches0           # shape (N0,), integer index into image1 keypoints or -1
    └── matching_scores0   # shape (N0,), optional from model but expected by hloc readers
```

Semantics:

- `N0` is the number of keypoints in the first image of the stored pair.
- `matches0[i] = j` means keypoint `i` in image0 matches keypoint `j` in image1.
- `matches0[i] = -1` means keypoint `i` is unmatched.
- `matching_scores0[i]` is the confidence score for keypoint `i`; hloc readers return scores only for matched indices.
- Sparse writer stores `matches0` as a short integer array and scores as half precision when available.

Use the public reader to avoid pair-order mistakes:

```python
from pathlib import Path
from hloc.utils.io import get_matches

matches, scores = get_matches(
    Path("outputs/feats-superpoint-n4096-r1024_matches-superglue_pairs-netvlad.h5"),
    "query/night/001.jpg",
    "db/000010.jpg",
)
# matches has shape (M, 2), with columns [idx_in_first_image, idx_in_second_image]
```

## Dense / LoFTR match HDF5 layout

`match_dense.main` first writes semi-dense correspondences for each image pair and then aggregates/assigns them to hloc-compatible `matches0` arrays.

Dense match file after successful assignment:

```text
matches-loftr_aachen_pairs-netvlad.h5
└── <pair_key>/
    ├── keypoints0          # raw LoFTR keypoints in image0, shape (M, 2)
    ├── keypoints1          # raw LoFTR keypoints in image1, shape (M, 2)
    ├── scores              # raw LoFTR scores, shape (M,)
    ├── matches0            # assigned keypoint matches, shape (N0,)
    └── matching_scores0    # assigned scores, shape (N0,)
```

Dense feature file after aggregation:

```text
feats_matches-loftr_aachen.h5
└── <image_name>/
    ├── keypoints           # aggregated/quantized LoFTR-derived keypoints
    └── score               # per-keypoint aggregate score; singular dataset name
```

Dense-specific notes:

- `features_ref` can anchor reference images to existing sparse keypoints. In that mode, the dense pipeline loads the reference keypoints and assigns LoFTR matches to them.
- `max_kps` limits aggregated keypoints per image. Use a smaller value for memory/storage constraints; use `None` for localization-style query matching where query keypoints should be preserved without top-k selection.
- `loftr` can produce many correspondences. `loftr_aachen` and `loftr_superpoint` quantize more aggressively for scalability.

## Cross-file consistency checklist

Before passing features/matches to reconstruction or localization, verify:

1. Pair-file names are exactly the same relative image names used as HDF5 feature group names.
2. Every first and second image in the pairs file has a feature group in the query/reference feature file used by the matcher.
3. Every requested pair has a match group in the match HDF5 under current or legacy pair naming.
4. Sparse match groups contain `matches0`; downstream hloc readers also expect `matching_scores0`.
5. `matches0` length equals the number of keypoints in the first image for that pair orientation.
6. All non-negative `matches0` values are less than the number of keypoints in the second image.
7. Global retrieval descriptor files use `global_descriptor`, not `descriptors`.
8. Manual HDF5 writers use relative POSIX image names, not OS-dependent absolute paths.

## Tiny pair-name debugger

```python
import h5py
from hloc.utils.parsers import names_to_pair, names_to_pair_old

name0 = "query/night/001.jpg"
name1 = "db/000010.jpg"
keys = [
    names_to_pair(name0, name1),
    names_to_pair(name1, name0),
    names_to_pair_old(name0, name1),
    names_to_pair_old(name1, name0),
]

with h5py.File("matches.h5", "r") as f:
    for key in keys:
        print(key, key in f)
```
