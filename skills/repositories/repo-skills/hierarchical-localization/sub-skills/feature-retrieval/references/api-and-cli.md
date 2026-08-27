# Feature Retrieval API and CLI Reference

This reference covers the public runtime surface for built-in hloc feature extraction, image-retrieval descriptors, sparse matching, and dense matching. It is self-contained: use installed `hloc` modules and the bundled helper script in this sub-skill rather than reading a source checkout.

## Verified public signatures

```text
extract_features.ImageDataset(root, conf, paths=None)
extract_features.main(conf: Dict, image_dir: pathlib.Path, export_dir: Optional[pathlib.Path] = None, as_half: bool = True, image_list: Union[pathlib.Path, List[str], NoneType] = None, feature_path: Optional[pathlib.Path] = None, overwrite: bool = False) -> pathlib.Path
match_features.main(conf: Dict, pairs: pathlib.Path, features: Union[pathlib.Path, str], export_dir: Optional[pathlib.Path] = None, matches: Optional[pathlib.Path] = None, features_ref: Optional[pathlib.Path] = None, overwrite: bool = False) -> pathlib.Path
match_features.match_from_paths(conf: Dict, pairs_path: pathlib.Path, match_path: pathlib.Path, feature_path_q: pathlib.Path, feature_path_ref: pathlib.Path, overwrite: bool = False) -> pathlib.Path
match_dense.main(conf: Dict, pairs: pathlib.Path, image_dir: pathlib.Path, export_dir: Optional[pathlib.Path] = None, matches: Optional[pathlib.Path] = None, features: Optional[pathlib.Path] = None, features_ref: Optional[pathlib.Path] = None, max_kps: Optional[int] = 8192, overwrite: bool = False) -> pathlib.Path
pairs_from_retrieval.main(descriptors, output, num_matched, query_prefix=None, query_list=None, db_prefix=None, db_list=None, db_model=None, db_descriptors=None)
```

`match_dense.main` returns a tuple `(features_path, matches_path)` in current hloc behavior even though the annotation is broad.

## ImageDataset contract

`ImageDataset(root, conf, paths=None)` is the loader used by `extract_features.main`.

Default preprocessing keys:

```python
{
    "globs": ["*.jpg", "*.png", "*.jpeg", "*.JPG", "*.PNG"],
    "grayscale": False,
    "resize_max": None,
    "resize_force": False,
    "interpolation": "cv2_area",
}
```

- If `paths is None`, images are discovered recursively under `root` with the configured globs and names are stored relative to `root` using POSIX separators.
- If `paths` is a file path, it is parsed as an image-list file. Empty lines and lines starting with `#` are ignored. Without intrinsics, each non-comment line starts with the image name.
- If `paths` is a Python iterable, each item is treated as an image name relative to `root`.
- Every listed image must exist at `root / name`; otherwise extraction fails before model execution.
- Images are read as RGB for color configs and single-channel for grayscale configs, optionally resized, converted to `float32`, channel-first, and scaled to `[0, 1]`.

## Built-in extractor configs

The keys below are accepted by `extract_features.confs` and by `python -m hloc.extract_features --conf ...`.

| Config | Output stem | Family | Main use | Important settings |
| --- | --- | --- | --- | --- |
| `superpoint_aachen` | `feats-superpoint-n4096-r1024` | local sparse | Strong default for outdoor/localization and many hloc examples. Pair with `superglue`, `superglue-fast`, `superpoint+lightglue`, or nearest-neighbor configs. | grayscale, resize max 1024, max 4096 keypoints, NMS radius 3 |
| `superpoint_max` | `feats-superpoint-n4096-rmax1600` | local sparse | Higher-resolution SuperPoint when images are good quality and extra compute/storage are acceptable. | grayscale, forced resize max 1600, max 4096 keypoints |
| `superpoint_inloc` | `feats-superpoint-n4096-r1600` | local sparse | Indoor/InLoc-style localization where larger resize is useful. | grayscale, resize max 1600, max 4096 keypoints, NMS radius 4 |
| `r2d2` | `feats-r2d2-n5000-r1024` | local sparse | R2D2 local features. | color, resize max 1024, max 5000 keypoints |
| `d2net-ss` | `feats-d2net-ss` | local sparse | D2-Net single-scale local features. | color, resize max 1600, single-scale model |
| `sift` | `feats-sift` | local sparse | Classical SIFT/RootSIFT-style baseline through the DoG extractor. | grayscale, resize max 1600 |
| `sosnet` | `feats-sosnet` | local sparse | DoG keypoints with SOSNet descriptors. | grayscale, resize max 1600 |
| `disk` | `feats-disk` | local sparse | DISK features, usually paired with `disk+lightglue`. | color, resize max 1600, max 5000 keypoints |
| `aliked-n16` | `feats-aliked-n16` | local sparse | ALIKED N16 features, usually paired with `aliked+lightglue`. | color, resize max 1024 |
| `dir` | `global-feats-dir` | global retrieval | Global descriptors for retrieval when DIR dependencies and weights are available. | resize max 1024 |
| `netvlad` | `global-feats-netvlad` | global retrieval | Standard hloc retrieval default; common for SfM and localization pair generation. | resize max 1024 |
| `openibl` | `global-feats-openibl` | global retrieval | OpenIBL global descriptors. | resize max 1024 |
| `megaloc` | `global-feats-megaloc` | global retrieval | MegaLoc global descriptors. | resize max 1024 |

Selection rules:

- Need retrieval pairs only: choose a global descriptor config such as `netvlad`, write `global-feats-*.h5`, then call `pairs_from_retrieval.main`.
- Need local SfM/localization features: choose a local sparse config. The safest default is `superpoint_aachen`; use `superpoint_inloc` for InLoc-style indoor scenes; use `disk` or `aliked-n16` only when matching with their corresponding LightGlue config.
- Need classical/external-friendly features: `sift` and `sosnet` are easier to inspect and can be useful baselines, but neural SuperPoint/DISK/ALIKED are more common in hloc examples.
- Need lower storage: keep half precision enabled in API calls, reduce `max_keypoints`, reduce `resize_max`, or restrict `image_list`.

## Feature extraction API and output naming

```python
from pathlib import Path
from hloc import extract_features

images = Path("images")
outputs = Path("outputs")
conf = extract_features.confs["superpoint_aachen"]
feature_path = extract_features.main(conf, images, outputs)
assert feature_path == outputs / "feats-superpoint-n4096-r1024.h5"
```

Naming rules:

- If `feature_path` is provided, `extract_features.main` writes exactly that path.
- Otherwise it writes `export_dir / (conf["output"] + ".h5")`.
- `overwrite=False` skips images whose HDF5 groups already exist; `overwrite=True` recomputes and replaces them.
- API default `as_half=True` converts floating-point prediction arrays to `float16` before writing. This saves disk but can reduce precision. If exact `float32` storage matters, pass `as_half=False`.

## Feature extraction CLI

```bash
python -m hloc.extract_features \
  --image_dir images \
  --export_dir outputs \
  --conf superpoint_aachen \
  --as_half
```

CLI options:

| Option | Required | Meaning |
| --- | --- | --- |
| `--image_dir PATH` | yes | Image root; HDF5 group names are relative to this root. |
| `--export_dir PATH` | yes | Output directory used when `--feature_path` is not provided. |
| `--conf NAME` | no | One of the extractor config names above; default `superpoint_aachen`. |
| `--as_half` | no | CLI flag enabling half precision. Note that the Python API defaults to `as_half=True`, while the CLI flag is off unless supplied. |
| `--image_list PATH` | no | Restrict extraction to listed relative image names. |
| `--feature_path PATH` | no | Exact feature HDF5 path; overrides `export_dir/conf['output']`. |

No CLI `--overwrite` flag is exposed for extraction in this version; use the Python API when recomputation is required.

## Retrieval descriptor pairing

Use `pairs_from_retrieval` only after extracting global descriptors that contain `global_descriptor` datasets.

```python
from pathlib import Path
from hloc import extract_features, pairs_from_retrieval

images = Path("images")
outputs = Path("outputs")
retrieval_conf = extract_features.confs["netvlad"]
descriptors = extract_features.main(retrieval_conf, images, outputs)
pairs = outputs / "pairs-netvlad.txt"
pairs_from_retrieval.main(descriptors, pairs, num_matched=20)
```

CLI:

```bash
python -m hloc.pairs_from_retrieval \
  --descriptors outputs/global-feats-netvlad.h5 \
  --output outputs/pairs-netvlad.txt \
  --num_matched 20
```

CLI options:

| Option | Required | Meaning |
| --- | --- | --- |
| `--descriptors PATH` | yes | Query/global descriptor HDF5. |
| `--output PATH` | yes | Text output with one `query reference` pair per line. |
| `--num_matched INT` | yes | Top database images retained per query after invalid/self-match filtering. |
| `--query_prefix STR [STR ...]` | no | Restrict queries to descriptor names beginning with one or more prefixes. |
| `--query_list PATH` | no | Restrict queries to listed image names. |
| `--db_prefix STR [STR ...]` | no | Restrict database descriptors to names beginning with one or more prefixes. |
| `--db_list PATH` | no | Restrict database descriptors to listed image names. |
| `--db_model PATH` | no | Use image names from a COLMAP model's `images.bin` as database names. |
| `--db_descriptors PATH` | no | Separate database descriptor HDF5; API also accepts a list of descriptor files. |

The retrieval score is a dot product between query and database descriptors. Descriptor normalization is the extractor/exporter's responsibility.

## Built-in sparse matcher configs

The keys below are accepted by `match_features.confs` and by `python -m hloc.match_features --conf ...`.

| Config | Output stem | Family | Best with | Notes |
| --- | --- | --- | --- | --- |
| `superpoint+lightglue` | `matches-superpoint-lightglue` | LightGlue | `superpoint_aachen`, `superpoint_max`, `superpoint_inloc` | Faster modern matcher for SuperPoint descriptors. |
| `disk+lightglue` | `matches-disk-lightglue` | LightGlue | `disk` | Match feature family must be DISK. |
| `aliked+lightglue` | `matches-aliked-lightglue` | LightGlue | `aliked-n16` | Match feature family must be ALIKED. |
| `superglue` | `matches-superglue` | SuperGlue | SuperPoint configs | Outdoor weights, 50 Sinkhorn iterations in the standard hloc config. |
| `superglue-fast` | `matches-superglue-it5` | SuperGlue | SuperPoint configs | Faster but lower-iteration SuperGlue. |
| `NN-superpoint` | `matches-NN-mutual-dist.7` | nearest neighbor | SuperPoint-like descriptors | Mutual nearest-neighbor plus distance threshold `0.7`. |
| `NN-ratio` | `matches-NN-mutual-ratio.8` | nearest neighbor | General local descriptors | Mutual nearest-neighbor plus ratio threshold `0.8`. |
| `NN-mutual` | `matches-NN-mutual` | nearest neighbor | General local descriptors | Mutual nearest-neighbor only. |
| `adalam` | `matches-adalam` | AdaLAM | Feature files with keypoints, descriptors, scales, orientations, and image sizes | Requires more input fields than SuperGlue/LightGlue/NN; check HDF5 schema before use. |

Selection rules:

- For common hloc localization/SfM: `superpoint_aachen` + `superglue` is a conservative default; `superpoint_aachen` + `superpoint+lightglue` is a modern faster alternative.
- For DISK or ALIKED extraction: use the corresponding `disk+lightglue` or `aliked+lightglue` matcher, not `superpoint+lightglue`.
- For dependency-light or custom descriptor matching: start with `NN-mutual` or `NN-ratio`.
- For features that include scale and orientation metadata: `adalam` can be considered; it is not a drop-in replacement for feature files that only contain keypoints/descriptors/scores.

## Sparse matching API and output naming

When `features` is a feature stem, not a file path:

```python
from pathlib import Path
from hloc import match_features

outputs = Path("outputs")
pairs = outputs / "pairs-netvlad.txt"
match_path = match_features.main(
    match_features.confs["superglue"],
    pairs,
    features="feats-superpoint-n4096-r1024",
    export_dir=outputs,
)
assert match_path == outputs / "feats-superpoint-n4096-r1024_matches-superglue_pairs-netvlad.h5"
```

Naming rules:

- If `features` is a path or an existing file, `matches` must also be provided. Use this for custom or cross-directory paths.
- If `features` is a stem string, `export_dir` is required and `features_q = export_dir / (features + ".h5")`.
- If `matches` is not provided in stem mode, hloc writes `export_dir / f"{features}_{conf['output']}_{pairs.stem}.h5"`.
- `features_ref` defaults to the same file as `features`; provide it for query-vs-reference feature files.
- `overwrite=False` skips pair groups that already exist in either direction or in the older underscore pair-name format.

## Sparse matching CLI

```bash
python -m hloc.match_features \
  --pairs outputs/pairs-netvlad.txt \
  --export_dir outputs \
  --features feats-superpoint-n4096-r1024 \
  --conf superglue
```

CLI options:

| Option | Required | Meaning |
| --- | --- | --- |
| `--pairs PATH` | yes | Text pairs file: one `image0 image1` pair per line. |
| `--export_dir PATH` | when `--features` is a stem | Directory containing `<features>.h5` and receiving the default match file. |
| `--features STR` | no | Feature stem or feature path; default `feats-superpoint-n4096-r1024`. |
| `--matches PATH` | no | Parser exposes this option, but use the Python API for reliable custom match-path handling. |
| `--conf NAME` | no | One of the sparse matcher config names above; default `superglue`. |

The CLI does not expose `features_ref` or `overwrite`; use the API for two-file query/reference matching or recomputation.

## Built-in dense matcher configs

The keys below are accepted by `match_dense.confs` and by `python -m hloc.match_dense --conf ...`.

| Config | Output stem | Family | Best use | Important settings |
| --- | --- | --- | --- | --- |
| `loftr` | `matches-loftr` | dense/semi-dense LoFTR | Best quality on small scenes where many points are acceptable. | grayscale, resize max 1024, `max_error=1`, `cell_size=1` |
| `loftr_aachen` | `matches-loftr_aachen` | dense/semi-dense LoFTR | More scalable LoFTR setting for Aachen-style workloads. | grayscale, resize max 1024, `max_error=2`, `cell_size=8` |
| `loftr_superpoint` | `matches-loftr_aachen` | dense/semi-dense LoFTR anchored to SuperPoint references | Use when matching/assigning LoFTR correspondences to existing SuperPoint keypoints. | grayscale, resize max 1024, `max_error=4`, `cell_size=4` |

Dense matching writes both a feature HDF5 and a match HDF5. Use it when LoFTR's image-pair model is desired instead of descriptor matching from a precomputed local feature file.

## Dense matching API and output naming

```python
from pathlib import Path
from hloc import match_dense

images = Path("images")
outputs = Path("outputs")
pairs = outputs / "pairs-netvlad.txt"
conf = match_dense.confs["loftr_aachen"]
features_path, matches_path = match_dense.main(conf, pairs, images, export_dir=outputs)
```

Naming rules:

- If `features` is `None`, hloc starts from the stem prefix `"feats_"`.
- In stem mode, `features_path = export_dir / f"{features}{conf['output']}.h5"`. With defaults and `loftr_aachen`, this is `outputs/feats_matches-loftr_aachen.h5`.
- In stem mode, if `matches` is `None`, `matches_path = export_dir / f"{conf['output']}_{pairs.stem}.h5"`. With `pairs-netvlad.txt` and `loftr_aachen`, this is `outputs/matches-loftr_aachen_pairs-netvlad.h5`.
- If `features` is a `Path`, `matches` must also be provided.
- `features_ref` can be a single feature HDF5 path or a list of reference feature HDF5 paths; use it to anchor dense matches to existing reference keypoints.
- `max_kps=8192` caps aggregated dense keypoints; pass `max_kps=None` for localization-style query matching where query keypoints should not be binned by top-k selection.

## Dense matching CLI

Prefer the Python API for dense matching when exact output paths matter. The CLI parser exposes:

| Option | Required | Meaning |
| --- | --- | --- |
| `--pairs PATH` | yes | Text pairs file. |
| `--image_dir PATH` | yes | Image root used for loading paired images. |
| `--export_dir PATH` | yes | Output directory for default feature/match naming when using API-equivalent stem behavior. |
| `--matches PATH` | no | Match output argument; provide an explicit path to avoid ambiguous defaults. |
| `--features STR` | no | Feature output stem; default derives from `loftr` in the CLI. |
| `--conf NAME` | no | One of `loftr`, `loftr_aachen`, `loftr_superpoint`; default `loftr`. |

Dense matching can load model weights and process image pairs; do not use it as a mere parser smoke test on large pair files.

## Config inspection helper

From any working directory, run:

```bash
python /path/to/this/sub-skill/scripts/inspect_hloc_configs.py --json
python /path/to/this/sub-skill/scripts/inspect_hloc_configs.py --section match
python /path/to/this/sub-skill/scripts/inspect_hloc_configs.py --section torch
```

The helper imports installed `hloc` config dictionaries and optionally reports Torch/CUDA availability. It does not run feature extraction, load images, or instantiate neural models.
