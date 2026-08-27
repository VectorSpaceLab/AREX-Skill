# Feature Retrieval Troubleshooting

Use this guide when hloc feature extraction, retrieval pairing, sparse matching, dense matching, or HDF5 inspection fails. Keep fixes local to the user's working data and installed package; this sub-skill does not require a source checkout.

## Fast triage commands

Inspect installed configs without running models:

```bash
python /path/to/feature-retrieval/scripts/inspect_hloc_configs.py --section all
python /path/to/feature-retrieval/scripts/inspect_hloc_configs.py --json
```

Check CLI parser imports:

```bash
python -m hloc.extract_features --help
python -m hloc.match_features --help
python -m hloc.match_dense --help
python -m hloc.pairs_from_retrieval --help
```

If `--help` fails, solve import dependencies before diagnosing data. Some hloc modules import shared utilities at module import time, so a missing dependency can break parser help before any model runs.

## `Could not find any image in root`

Likely causes:

- `image_dir` points to the wrong folder.
- Images use extensions outside the default globs: `*.jpg`, `*.png`, `*.jpeg`, `*.JPG`, `*.PNG`.
- An `image_list` was passed but entries are not relative to `image_dir`.
- A list file is empty after removing comments and blank lines.

Fixes:

```python
from pathlib import Path
root = Path("images")
print(root.resolve())
print(sum(1 for _ in root.rglob("*.jpg")))
print(sum(1 for _ in root.rglob("*.png")))
```

For list-driven extraction, rewrite names as relative POSIX paths:

```text
query/0001.jpg
db/000010.jpg
```

Do not put absolute paths in hloc image lists unless a specific downstream parser explicitly expects them; feature HDF5 names should remain relative.

## `Image <name> does not exist in root`

`ImageDataset` validates every listed image as `image_dir / name`.

Checklist:

1. Confirm case-sensitive spelling and extension.
2. Confirm the list path is not a pair file; image lists have one image name per line, while pair files have two names per line.
3. Confirm there is no leading `./` mismatch in one artifact and not another.
4. Confirm all downstream pair files use the same exact relative names.

## Feature file not created or unexpectedly skipped

Possible causes:

- `feature_path` already contains image groups and `overwrite=False`, so extraction skips them.
- `export_dir` differs from the directory later used for matching.
- The CLI did not receive `--as_half`; API and CLI differ in half-precision defaults.
- The process stopped during model download or import before writing any HDF5 groups.

Checks:

```python
from pathlib import Path
from hloc.utils.io import list_h5_names
p = Path("outputs/feats-superpoint-n4096-r1024.h5")
print(p.exists(), p)
print(sorted(list_h5_names(p))[:10] if p.exists() else "missing")
```

If only some images are missing and recomputation is intended, use the API with `overwrite=True` or write to a new `feature_path`.

## Missing or wrong global retrieval descriptors

Symptoms:

- `pairs_from_retrieval` raises a key error for `global_descriptor`.
- Pair file has fewer pairs than expected.
- Pair file contains no database images for a prefix/list.

Fixes:

1. Use a global config (`dir`, `netvlad`, `openibl`, `megaloc`), not a local sparse config.
2. Confirm each image group contains `global_descriptor`.
3. Confirm `query_prefix`, `db_prefix`, `query_list`, and `db_list` match HDF5 image names exactly.
4. If using separate query/database files, pass `db_descriptors`.
5. Remember retrieval avoids self-matches and filters negative dot-product scores.

Inspection snippet:

```python
import h5py
with h5py.File("outputs/global-feats-netvlad.h5", "r") as f:
    name = next(iter(f.keys()))
    # If image names contain '/', traverse with a full known image name instead of only top-level keys.
```

For robust name listing, prefer `hloc.utils.io.list_h5_names`.

## Missing feature groups during sparse matching

Symptoms:

- HDF5 `KeyError` for an image name.
- `FileNotFoundError: Query feature file ...` or `Reference feature file ...`.
- Matching runs but outputs fewer pair groups than the pair file.

Causes and fixes:

- Pair file names do not match feature HDF5 names. Regenerate pairs from the same image names used for extraction.
- `features` was passed as a stem string but `export_dir` points to the wrong folder. If uncertain, pass full `Path` objects for both `features` and `matches` through the Python API.
- `features_ref` is needed for query-vs-reference matching but was omitted.
- Existing match groups are skipped when `overwrite=False`; pass `overwrite=True` to recompute.

Reliable API pattern for explicit paths:

```python
from pathlib import Path
from hloc import match_features

match_features.main(
    match_features.confs["superglue"],
    pairs=Path("outputs/pairs-netvlad.txt"),
    features=Path("outputs/query-features.h5"),
    features_ref=Path("outputs/reference-features.h5"),
    matches=Path("outputs/query-reference-matches.h5"),
    overwrite=True,
)
```

## Match HDF5 missing a requested pair group

Symptoms:

- `Could not find pair (name0, name1)... Maybe you matched with a different list of pairs?`
- Manual HDF5 inspection appears not to show the pair.
- Reconstruction/localization says there are no matches for a retrieved database image.

Checklist:

1. Check whether the pair was actually present in the pairs text file used for matching.
2. Check both current and legacy pair names:

   ```python
   import h5py
   from hloc.utils.parsers import names_to_pair, names_to_pair_old
   name0 = "query/0001.jpg"
   name1 = "db/000010.jpg"
   candidates = [
       names_to_pair(name0, name1),
       names_to_pair(name1, name0),
       names_to_pair_old(name0, name1),
       names_to_pair_old(name1, name0),
   ]
   with h5py.File("outputs/matches.h5", "r") as f:
       print({c: c in f for c in candidates})
   ```

3. Remember current pair keys contain `/` between the two slash-sanitized image names, so HDF5 viewers show nested groups.
4. If matching skipped duplicates, the reverse orientation may exist instead of the listed orientation. Use `hloc.utils.io.get_matches` rather than manual indexing.
5. If the pair was previously computed with a different pair list stem, the default match filename may be different.

## `matches0` / `matching_scores0` schema errors

Symptoms:

- `KeyError: matching_scores0` while reading matches.
- Downstream code rejects `matches0` shape or dtype.
- Non-negative match indices exceed the keypoint count of the second image.

Expected sparse schema:

```text
<pair_key>/matches0           shape (N0,), integer, -1 for unmatched
<pair_key>/matching_scores0   shape (N0,), float score
```

Fixes:

- For manually written files, add `matching_scores0`; hloc readers expect it.
- Ensure `len(matches0)` equals the number of keypoints for image0 in that pair orientation.
- Ensure every `matches0[i] >= 0` is `< number_of_keypoints_image1`.
- Use the same pair orientation when comparing lengths and indices.
- For dense LoFTR outputs, confirm assignment completed; raw `keypoints0`, `keypoints1`, and `scores` alone are not enough for hloc sparse consumers.

## Descriptor shape or dtype mismatch

Common expectations:

- Local feature descriptors are usually `D x N`, not `N x D`.
- Keypoints are `N x 2` in original image coordinates.
- `image_size` is `(width, height)`.
- Global descriptors are one vector per image under `global_descriptor`.
- hloc usually casts loaded sparse features to float tensors during matching, so `float16` HDF5 is acceptable for built-in pipelines.

If a custom or external exporter produced files, route to `../custom-interop/` for validation and conversion guidance.

## Model download, cache, or missing dependency failures

Typical symptoms:

- Import errors for model packages used by specific configs.
- HTTP/download failures while loading SuperPoint, SuperGlue, NetVLAD, DISK, ALIKED, LightGlue, LoFTR, or other weights.
- Offline environment has the package installed but no cached weights.

Fixes:

1. Run the config inspection helper first; it imports config dictionaries without instantiating models.
2. Verify that the selected config's optional dependencies are installed. For example, LightGlue configs require the LightGlue package; LoFTR uses Kornia's LoFTR implementation; some global descriptors require their own model packages or weight files.
3. If the environment is offline, pre-populate the relevant model cache or choose a dependency-light config such as nearest-neighbor matching over already exported descriptors.
4. If a download partially failed, remove only the incomplete cached weight file and retry in a network-enabled environment.
5. Avoid running dense or dataset-scale model loading just to inspect configuration names.

## CUDA, CPU, and memory problems

hloc selects `cuda` when `torch.cuda.is_available()` is true; otherwise it uses CPU. CUDA is an accelerator, not required for the config dictionaries or HDF5 format checks.

Problems and mitigations:

- GPU out of memory: reduce `resize_max`, reduce `max_keypoints`, reduce dense `max_kps`, split the image or pair list, or use `superglue-fast`/LightGlue/nearest-neighbor instead of heavier settings.
- CPU is very slow: use smaller image lists for smoke tests; run full extraction/matching on a machine with CUDA if the dataset is large.
- CUDA detected but undesirable: run in an environment where CUDA is hidden/disabled before importing hloc and torch, or use a CPU-only torch installation.
- Dense LoFTR too large: prefer `loftr_aachen` over `loftr`, reduce pair count, or switch to sparse feature extraction and sparse matching.

## CLI path and output-name surprises

- `extract_features` API defaults to `as_half=True`; its CLI requires `--as_half` to enable half precision.
- `match_features` default output name uses the feature stem, matcher output stem, and pairs-file stem: `<features>_<match_output>_<pairs.stem>.h5`.
- `match_dense` writes both feature and match files; use the Python API when exact output paths matter.
- Some CLI parsers expose fewer controls than the Python APIs. Use APIs for `overwrite`, `features_ref`, exact match paths, or query/reference feature split.

## Safe recovery sequence

When a feature/match task fails mid-run:

1. Do not delete existing HDF5 files immediately.
2. List existing image or pair groups.
3. Re-run with `overwrite=False` to skip completed entries if the failure was transient.
4. Re-run with explicit paths and `overwrite=True` only when the previous contents are known to be wrong.
5. If disk space caused the failure, keep half precision, lower keypoint counts, move outputs to larger storage, or split outputs by image subset.
