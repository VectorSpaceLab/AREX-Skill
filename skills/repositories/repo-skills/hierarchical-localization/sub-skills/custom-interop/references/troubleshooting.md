# Custom interop troubleshooting

Use this guide after validation or HLoc runtime errors involving custom modules, external HDF5 files, retrieval pairs, image lists, or pose/list parsing.

## Dynamic-load errors

### Symptom: `ModuleNotFoundError` for `hloc.extractors.<name>` or `hloc.matchers.<name>`

Likely causes:

- Config `model.name` does not match the module basename.
- The module is not importable in the Python environment running HLoc.
- The custom module lives outside the `hloc.extractors` or `hloc.matchers` namespace and was not exposed through a wrapper package or editable fork.

Recovery:

1. Confirm the config path:
   - extractor config uses `"model": {"name": "my_extractor"}` → imports `hloc.extractors.my_extractor`.
   - matcher config uses `"model": {"name": "my_matcher"}` → imports `hloc.matchers.my_matcher`.
2. In the same Python environment, test a direct import:
   ```bash
   python - <<'PY'
   import importlib
   print(importlib.import_module('hloc.extractors.my_extractor'))
   print(importlib.import_module('hloc.matchers.my_matcher'))
   PY
   ```
3. Prefer installing a fork or wrapper package in editable mode instead of patching a long-lived environment in place.

### Symptom: `AssertionError` showing a list of classes from `dynamic_load`

Likely causes:

- The module defines zero `BaseModel` subclasses.
- The module defines more than one class that subclasses `BaseModel`.
- The only subclass is imported from another module, not defined in the module being loaded.

Recovery:

- Keep exactly one concrete `BaseModel` subclass in the module named by `model.name`.
- Move helper `BaseModel` subclasses into separate modules, or make helpers inherit from `torch.nn.Module` instead.
- Ensure the subclass is defined in that module, not only imported there.

### Symptom: import works, but model initialization fails only during extraction/matching

Likely causes:

- Optional heavy dependency is imported inside `_init` and is missing.
- Weight path or model-name option is invalid.
- The config was merged into `default_conf` but the custom `_init` expects another key name.

Recovery:

- Print or log the merged `conf` in a disposable run.
- Keep optional dependency checks explicit in `_init` error messages.
- Confirm `default_conf` contains every key used by `_init` and `_forward` unless the caller always supplies it.

## Required input mismatches

### Symptom: `AssertionError: Missing key <name> in data`

Likely causes:

- `required_inputs` lists a key that the HLoc dataset does not create.
- The feature HDF5 file is missing a dataset needed by the matcher.
- A matcher expects `scores`, `scales`, or `oris`, but the external feature file only has `keypoints` and `descriptors`.

Recovery:

1. Map matcher inputs to feature HDF5 datasets:
   - `keypoints0`/`keypoints1` require `keypoints` in both feature groups.
   - `descriptors0`/`descriptors1` require `descriptors` in both feature groups.
   - `scores0`/`scores1` require `scores` in both feature groups.
   - `scales0`/`scales1` require `scales` in both feature groups.
   - `oris0`/`oris1` require `oris` in both feature groups.
   - `image0`/`image1` require `image_size` so HLoc can synthesize image-shaped tensors.
2. Validate the file:
   ```bash
   python sub-skills/custom-interop/scripts/validate_hloc_formats.py --features features.h5 --strict
   ```
3. If the field is not meaningful for the custom matcher, remove it from `required_inputs`. If a built-in matcher needs it, export the missing dataset.

## Descriptor shape and dtype problems

### Symptom: nearest-neighbor matcher returns shape errors or very poor matches

Likely causes:

- Sparse descriptors were exported as `(N, D)` instead of HLoc's `(D, N)` convention.
- Descriptor count does not match the keypoint count.
- Descriptors are integer-coded or unnormalized when the matcher expects float descriptors and dot-product similarity.

Recovery:

- Local descriptors should be numeric 2-D arrays shaped `(D, N)`.
- If an external model emits `(N, D)`, transpose before writing HDF5.
- Keep descriptor dtype as `float32` or `float16` unless a custom matcher explicitly documents otherwise.
- Validate descriptor/keypoint consistency:
  ```bash
  python sub-skills/custom-interop/scripts/validate_hloc_formats.py --features features.h5 --strict
  ```

### Symptom: retrieval pair generation fails while stacking descriptors

Likely causes:

- Some image groups lack `global_descriptor`.
- Global descriptors have inconsistent dimensions.
- Descriptor groups use image names that differ from query/database list names.

Recovery:

- Ensure every image used for retrieval has a one-dimensional `global_descriptor` with the same length.
- Validate retrieval names against descriptor groups:
  ```bash
  python sub-skills/custom-interop/scripts/validate_hloc_formats.py \
    --features global-descriptors.h5 \
    --retrieval pairs-query-db.txt
  ```

## Pair naming and missing match groups

### Symptom: `Could not find pair (name0, name1)... Maybe you matched with a different list of pairs?`

Likely causes:

- The match HDF5 group used a different pair-name convention.
- The retrieval/pairs text file used names with prefixes that differ from the feature and match files.
- The pair exists only for a different image order and was not written with a convention HLoc can reverse-detect.
- External export used basename-only image names while HLoc uses relative paths.

Recovery:

1. Compute the current HLoc pair path:
   ```python
   pair = name0.replace('/', '-') + '/' + name1.replace('/', '-')
   ```
2. Also check the legacy path:
   ```python
   pair_old = name0.replace('/', '-') + '_' + name1.replace('/', '-')
   ```
3. Validate matches against the pair file:
   ```bash
   python sub-skills/custom-interop/scripts/validate_hloc_formats.py \
     --features features.h5 \
     --matches matches.h5 \
     --retrieval pairs-query-db.txt
   ```
4. Rewrite the match file with current pair names if the validator reports missing groups.

## Parser assertions and list-file errors

### Symptom: assertion failure while parsing image lists

Likely causes:

- The path or glob for an image list matched no files.
- The list file has only blank/comment lines.
- A query intrinsics list line is malformed.

Recovery:

- Plain image lists should contain one image name per non-comment line.
- Query intrinsics lists should use:
  ```text
  image_name CAMERA_MODEL width height params...
  ```
- Validate lists before running localization:
  ```bash
  python sub-skills/custom-interop/scripts/validate_hloc_formats.py --image-list queries.txt
  ```

### Symptom: retrieval parser fails with unpacking errors

Likely causes:

- A retrieval/pairs line has fewer or more than two whitespace-separated fields.
- The file contains comment lines; retrieval parser does not treat `#` as a comment marker.
- Image names contain spaces.

Recovery:

- Use exactly two tokens per non-empty retrieval line: `query_name reference_name`.
- Remove comments from retrieval/pair files.
- Replace spaces in file names before using HLoc.

## Match array range errors

### Symptom: downstream code indexes outside keypoint arrays or validation reports out-of-range matches

Likely causes:

- `matches0` references keypoint indices not present in image1.
- `matches0` length does not equal the keypoint count for image0.
- Match file was generated against a different feature file or after top-k keypoint filtering.

Recovery:

- Validate matches with the exact feature file used downstream:
  ```bash
  python sub-skills/custom-interop/scripts/validate_hloc_formats.py \
    --features features.h5 \
    --matches matches.h5 \
    --retrieval pairs.txt \
    --strict
  ```
- Regenerate matches whenever keypoints are filtered, sorted, or reindexed.
- Keep feature and match file basenames/version tags tied together in the output directory.

## Pose/list output confusion

### Symptom: a pose result file cannot be consumed by an external evaluator

Likely causes:

- The evaluator expects `qx qy qz qw` but HLoc writes `qw qx qy qz`.
- The evaluator expects world-from-camera while HLoc writes camera-from-world.
- The output name was changed by basename-only or camera-name-prepending behavior.

Recovery:

- Treat HLoc result lines as:
  ```text
  image_name qw qx qy qz tx ty tz
  ```
- Convert quaternion order and pose direction only if the external evaluator requires it.
- Preserve the same image naming policy from query list through results.

## When to route away from custom interop

- If the user only needs to choose existing SuperPoint, DISK, ALIKED, NetVLAD, SuperGlue, LightGlue, nearest-neighbor, AdaLAM, or LoFTR configs, route to [feature-retrieval](../../feature-retrieval/SKILL.md).
- If the files validate and the user now wants SfM, triangulation, or query localization, route to [mapping-localization](../../mapping-localization/SKILL.md).
- If the task is dataset-specific or benchmark-scale, route to [dataset-pipelines](../../dataset-pipelines/SKILL.md).
