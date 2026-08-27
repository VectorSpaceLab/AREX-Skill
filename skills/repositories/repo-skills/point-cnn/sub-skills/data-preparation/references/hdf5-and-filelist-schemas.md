# HDF5, file-list, and PLY schemas

The legacy loader has no schema-version field. Treat the key names, ranks,
parallel first dimensions, and effective feature width below as the operating
contract. Run `validate_pointcnn_h5.py` before handing a file list to a model.

## Classification HDF5

Required datasets:

| Key | Shape | Dtype and meaning |
|---|---|---|
| `data` | `[B,N,C]` | Floating point; `B > 0`, `N > 0`, `C >= 3`. The first three channels are XYZ and remaining channels are features. |
| `label` | `[B]` or `[B,1]` | Integer object-class ids, one per sample. Use nonnegative contiguous ids for settings whose logits or weights index labels. |

Optional dataset:

| Key | Shape | Dtype and meaning |
|---|---|---|
| `normal` | `[B,N,3]` | Floating point normals parallel to `data`. `load_cls` concatenates it to `data` along the last axis, so its presence changes the effective feature width by three. |

`load_cls(filelist)` uses `basename(line)` and joins that basename to the
classification list's directory. Thus `train/foo.h5` in a parent-level list
is not resolved as `parent/train/foo.h5`; use a list beside the files or list
basenames. It concatenates all files along B and does not check class ranges,
feature widths, point counts, or finite values. The validator does.

## Segmentation HDF5

Required datasets:

| Key | Shape | Dtype and meaning |
|---|---|---|
| `data` | `[B,N,C]` | Floating point, `C >= 3`; only the first `data_num[i]` points are active. |
| `data_num` | `[B]` | Integer count with `1 <= data_num[i] <= N`. |
| `label` | `[B]` or `[B,1]` | Integer sample/category/room placeholder. It is loaded but is often not the per-point target. |
| `label_seg` | `[B,N]` | Integer per-point target. Only `label_seg[i, :data_num[i]]` is valid. |

Optional reconstruction dataset:

| Key | Shape | Meaning |
|---|---|---|
| `indices_split_to_full` | `[B,N]` | One integer source-point index per padded point. Used by S3DIS and Semantic3D. |
| `indices_split_to_full` | `[B,N,2]` | Integer `(room_id, point_id)` pair per padded point. Used by ScanNet segmentation. |

Require the optional key consistently across a list when reconstruction is
needed. Do not mix one-dimensional and two-dimensional conventions. Validate
active indices only; padded indices are not observations. The source bound is
external, so supply `--index-size` for one-dimensional indices or the point-id column of
pairs; add `--index-group-count` for a pair's room bound, or use
`--room-sizes FILE` for exact two-dimensional bounds.

`load_seg(filelist)` casts `data` to float32, `label` and `label_seg` to int64,
and `data_num` to int32, then concatenates files on B. It returns `None` for
indices only when no input file has that key. It does not enforce consistent
N/C or index rank, so list-level validation must enforce those properties.

## Rank, dtype, and value rules

- `data` must be rank 3, numeric floating point, finite, and have positive B,
  N, and at least three channels.
- Labels, counts, and indices must be integer dtypes, not float, bool, string,
  or object. Labels may be `[B]` or `[B,1]`; all other shapes above are exact.
- `data_num` must have one value per sample and may not be zero or exceed N.
- Classification labels must be nonnegative; `--class-count K` additionally
  requires every label to be less than K.
- Segmentation active `label_seg` values must be nonnegative;
  `--class-count K` checks active values against K. Padded labels are ignored.
- Optional active indices must be nonnegative. `--index-size M` checks every
  one-dimensional active index is below M. `--room-sizes FILE` reads one
  positive integer per non-comment line and checks each active pair's room and
  point bounds.
- For a list, all files must have the same task, N, effective C, and optional
  index presence/rank. Classification effective C includes an optional normal
  width of three. This mirrors the legacy concatenation boundary.

The validator intentionally does not infer class count, coordinate order,
RGB/intensity scale, source index bounds, or whether normalization was already
performed. Supply those facts from the selected dataset card and model setting.

## Flat and nested lists

A runtime list is UTF-8 text with one nonempty path per line. Blank lines,
comments, shell quoting, and inline annotations are not valid legacy list
syntax. Use portable relative paths and avoid absolute paths in generated
lists.

### Classification list

```text
train_000.h5
train_001.h5
```

The inspector and validator reproduce the basename lookup used by the loader.

### Flat segmentation list

```text
./train/zero_000.h5
./train/zero_001.h5
```

Segmentation entries are joined to the directory of the list that contains
them, preserving relative components.

### Nested segmentation list

Top level:

```text
./filelists/train_group_000.txt
./filelists/train_group_001.txt
```

Child list:

```text
../train/zero_000.h5
../train/half_000.h5
```

The legacy `is_h5_list()` treats a list as flat only when every raw line ends
in `.h5`. A blank, comment, or child-list line changes the mode. Never mix
HDF5 and child-list entries. Child entries resolve relative to their child
list, not the top-level list. The trainer rotates through one child list at a
time; validation/test lists should normally be flat.

## PLY helpers

PLY is a diagnostic output format, never a model input. The legacy helpers
accept points `[N,3]`, with parallel normals `[N,3]` or colors. Batch helpers
truncate to `data_num`; property helpers map zero to black and need a positive
stable maximum. The writer emits a binary vertex-only PLY and creates its
parent directory, so use an explicit new visualization root and inspect one
small output before generating a tree. Some legacy color call sites pass
already-scaled RGB even though the base writer multiplies colors by 255; check
one file rather than assuming color correctness. The bundled scripts do not
write PLY.

## Validation and repair policy

Run the list inspector first, then validate every resolved HDF5. A passing
schema check proves only that the file is structurally consumable. It does not
prove TensorFlow 1.x graph execution, CUDA/custom-op availability, FPS, class
semantics, coordinate orientation, or source-index provenance. Do not reshape,
relabel, add placeholder datasets, or overwrite a malformed file in place;
reconvert into a new approved destination and retain the mapping and logs.
