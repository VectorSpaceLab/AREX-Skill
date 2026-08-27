# CLI reference

## Entry points and model resolution

Package metadata maps:

```text
stardist-predict2d = stardist.scripts.predict2d:main
stardist-predict3d = stardist.scripts.predict3d:main
```

The bundled adapters in `../scripts/` can be run directly with Python. Their
help path parses before importing TensorFlow, StarDist, or optional packages:

```bash
python /path/to/predict2d.py --help
python /path/to/predict3d.py --help
```

A model selector is deliberately ambiguous only for a plain token:

- If the expanded selector is an existing directory, it must contain
  `config.json` and at least one `.h5` weight file. It is loaded as a local
  model with the matching dimensionality.
- A plain token such as `2D_versatile_fluo`, `2D_demo`, or `3D_demo` enters
  `from_pretrained`. StarDist may download and cache that registered model;
  approve network, cache space, and checksum/resource provenance first.
- A missing path-like selector (absolute, contains a separator, starts with
  `.`/`~`, or looks like an archive/model file) is rejected. This prevents a
  misspelled local path from silently becoming a network download.
- Do not pass a parent directory containing many model folders. Do not mix a
  2D model with the 3D command or vice versa. `thresholds.json` is recommended
  for a local model because it stores calibrated defaults.

## Flags

| Flag | Contract |
|---|---|
| `-i, --input PATH...` | One or more readable images. The adapters use `tifffile`; the 3D adapter requires `.tif`/`.tiff`. |
| `-m, --model SPEC` | Required local directory or intentional registered pretrained name. |
| `-o, --outdir DIR` | Output directory, created if absent. A symlinked output file cannot redirect writes outside it. |
| `--outname TEMPLATE` | One filename, default `{img}.stardist.tif`; only `{img}` is supported. Absolute, nested, traversal, unsupported-suffix, duplicate, and input-equal outputs are rejected. |
| `--axes AXES` | Explicit axes matching array rank. 2D requires exactly `Y,X` with optional `C`; 3D requires exactly `Z,Y,X` with optional `C`. Permutations are allowed when the model API supports them. |
| `--n-tiles N...` / `--n_tiles N...` | Exactly two integers for 2D or three for 3D. Tiling controls memory and edge handling; it does not fix invalid axes. |
| `--pnorm PMIN PMAX` | Percentiles for `csbdeep.normalize`, default `1 99.8`. Require `0 <= PMIN < PMAX <= 100`. |
| `--prob-thresh VALUE` / `--prob_thresh VALUE` | Optional object probability threshold; omitted uses the model default. |
| `--nms-thresh VALUE` / `--nms_thresh VALUE` | Optional non-maximum-suppression threshold; omitted uses the model default. |
| `-v, --verbose` | Print model, input shape/axes, prediction, and output progress. |
| `--overwrite` | Permit replacing a known existing output after checking it. It does not permit input overwrite or a symlink escape. |
| `-h, --help` | Show flags and exit before runtime imports. |

The original 0.9.2 scripts use underscore spellings. The adapted scripts keep
those aliases and also accept hyphen spellings. They keep only `--model` as a
required selector; axes, tiling, normalization, and thresholds can be combined.

## Input/output conventions

### 2D

Rank 2 is grayscale `YX`; rank 3 is one-channel-axis data, default `YXC`.
Declare `XY`, `CXY`, or another permutation only when its semantics are
correct. Time, batch, and multiple samples are not implicit inputs. Split them
or use the model workflow with explicit axes. The adapter normalizes the whole
image with the selected percentiles, calls `predict_instances`, and writes the
returned spatial label array as an integer TIFF without the channel axis.

### 3D

Rank 3 is `ZYX`; rank 4 is one-channel-axis data, default `ZYXC`. A physical
voxel spacing is not inferred by the file CLI. Use the 3D API's `scale` and
anisotropy contract when physical coordinates matter, and pass the same
Z/Y/X spacing to OBJ export. The output label array has spatial dimensions
only.

The API behind both CLIs is:

```python
model.predict_instances(
    img, axes=None, normalizer=None, sparse=True,
    prob_thresh=None, nms_thresh=None, scale=None, n_tiles=None,
    show_tile_progress=True, verbose=False, return_labels=True,
    predict_kwargs=None, nms_kwargs=None, overlap_label=None,
    return_predict=False,
)
```

The CLIs expose a conservative file subset. Route `normalizer`, `scale`, raw
probability/distance outputs, multiclass results, and
`predict_instances_big` to the owning [2D](../../2d-workflows/SKILL.md) or
[3D](../../3d-workflows/SKILL.md) workflow.

## Safe examples

```bash
stardist-predict2d -i raw/sample.tif -m /data/models/2D_demo \
  --axes YX --pnorm 1 99.8 --outdir results

stardist-predict3d -i raw/volume.tiff -m /data/models/3D_demo \
  --axes ZYX --n-tiles 1 2 2 --outdir results
```

Quote untrusted paths, inspect shell-expanded input lists, and keep raw images,
model files, and generated labels in distinct directories. Confirm output
shape/dtype before sending labels to ImageJ, QuPath, or training.
