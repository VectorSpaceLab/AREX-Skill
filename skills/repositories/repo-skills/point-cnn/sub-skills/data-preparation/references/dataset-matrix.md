# PointCNN dataset matrix

This is a preparation and validation matrix, not a download manifest. Treat
raw archives, benchmark splits, labels, and preprocessed pickles as external
inputs. Confirm their provenance, license/terms, integrity, and exact layout
before any conversion. The bundled scripts never acquire or convert data.

## Classification datasets

| Dataset | Raw and conversion contract | Lists, labels, and boundaries |
|---|---|---|
| **ModelNet40** | The supplied point-HDF5 archive contains `data` with XYZ and may contain a separate `normal` dataset. The legacy classification loader concatenates `normal` to `data` on the final axis. Common settings use 1024 sampled points and six channels after concatenation. | Use separate train and test/validation HDF5 lists. There are 40 object classes. A classification list is resolved by taking `basename(line)` and joining it to the list directory; put the list beside its HDF5 files or list basenames. |
| **ScanNet objects** | Scene extraction reads scene PLY/JSON plus a label table and writes object text files with six numeric values per row (`xyzrgb`) and a class suffix in the filename. Classification conversion samples 2048 points, shuffles, normalizes RGB from 0..255 to approximately -0.5..0.5, and writes `data[B,2048,6]` and `label[B]`. | The checked-in setting uses 17 classes. Keep train/test lists and the label mapping from the benchmark; do not infer class ids from directory order. Reject empty objects and files without exactly six numeric columns before conversion. Scene extraction and PLY parsing are writes/large reads, not smoke tests. |
| **TU-Berlin** | SVG paths are sampled into 1024 points with three point coordinates and three normals, producing `data[B,1024,6]`. Optional augmentation removes path portions and applies deformation. HDF5 files are written per fold and `categories.txt` records category ids. | There are three folds; the setting uses 250 classes and 512 points at training time. Category ids are assigned by first appearance in the SVG file list. SVG parse failures are skipped and reported. Preserve that report and do not treat a short fold as complete. |
| **MNIST** | The converter reads IDX data from a raw directory, drops zero pixels, samples a configurable number of nonzero pixels (default 256), uses XYZ-like coordinates plus one normalized intensity channel, and writes `data[B,256,4]` and `label[B]`. It emits train/test HDF5 lists. | There are 10 digit classes. A zero-pixel image has no sampling probability distribution and must be rejected before conversion. The checked-in setting samples 160 points. HDF5 is fixed-width; no `data_num` key is used. Optional PLY is a write-heavy diagnostic. |
| **CIFAR-10** | The converter reads the raw Python batch files, expands each 32x32 RGB image to 1024 points, adds a tiny random middle coordinate, normalizes RGB to approximately -0.5..0.5, and writes `data[B,1024,6]` and `label[B]`. It loads the five training batches together, so memory can be substantial. | There are 10 classes with separate train/test lists. Check raw batch keys, image/label lengths, and RGB planes before conversion. Use a bounded fixture first; do not run the full conversion merely to prove imports. |
| **Quick Draw** | The normal classification route reads a category list and per-category NPZ stroke arrays at runtime. Strokes are padded/mapped to points and normals on the fly, producing six input channels; it is not a normal HDF5 conversion path. | The checked-in setting uses 345 categories and 512 points. Validate category order, required train/valid arrays, nonempty strokes, and available RAM. A malformed category can break concatenation; per-sample PLY is optional and potentially large. Network acquisition of all category archives is never a default. |

## Segmentation datasets

| Dataset | Raw and conversion contract | Lists, labels, and boundaries |
|---|---|---|
| **ShapeNet Parts** | Parallel train/validation/test category directories contain point text and one `.seg` label per point. The converter checks equal lengths, subtracts the global minimum part id, offsets each category's part range into one global space, pads samples, and writes `data[B,N,3]`, `data_num[B]`, `label[B]` (object category), and `label_seg[B,N]`. | The checked-in setting uses 50 part classes. Use `train_files.txt`, `val_files.txt`, `test_files.txt`, and optionally their train/validation combination. No reconstruction index is emitted. Every point row and label row must match exactly. `categories.txt` is the mapping record. |
| **S3DIS** | Label preparation first creates per-room `xyzrgb.npy` and `label.npy`. Conversion aligns XYZ to the room bottom center, permutes coordinates to `x,z,y`, normalizes RGB to approximately -0.5..0.5, grids and merges blocks, emits zero and half-block offsets, and splits/pads to a default maximum of 8192 points. | There are 13 semantic classes. HDF5 contains `data[B,N,6]`, `data_num`, `label`, `label_seg`, and `indices_split_to_full[B,N]`, where the index is an original room-point index. File-list generation supports held-out Area validation and child lists grouped by HDF5 count. `.labels` and `.dataset` are cache markers, not completion proofs. |
| **ScanNet segmentation** | The preparation path expects preprocessed train/test per-room XYZ arrays and labels. It aligns rooms to their bottom center, block partitions, grid-balances, splits/pads to a default maximum of 8192, permutes to `x,z,y`, and writes `data[B,N,3]`, `data_num`, `label`, `label_seg`, and `indices_split_to_full[B,N,2]`. | The pair index is `(room_id, original_point_id)`. The checked-in setting uses 21 semantic classes and treats label zero as an ignored class through its weights. Generated train/test lists can reference child lists for rotating training groups. Validate pair bounds against the original room sizes before merging. |
| **Semantic3D** | Raw rows contain XYZ, intensity, and RGB. Rows with raw label zero are removed; remaining labels are shifted down by one. Conversion uses default block size 5.0, grid size 0.1, zero/half offsets, and a maximum of 8192 points. It writes `data[B,N,7]` as x,z,y plus normalized RGB and intensity, `data_num`, `label`, `label_seg`, and `indices_split_to_full[B,N]`. | There are eight semantic classes in the checked-in setting. Keep train/validation/test HDF5 directories and their lists; training may use child lists. The one-dimensional index points to the source cloud after the zero-label rows were removed. The acquisition and decompression route is documented as roughly 900 GB and is never a bundled/default action. `.unpacked` markers can hide partial extraction; inspect actual files. |

## Cross-dataset contracts

- Segmentation arrays are padded to N. Only `data[i, :data_num[i]]` and
  `label_seg[i, :data_num[i]]` are observations. Padded labels and indices have
  no meaning and must not be scored or merged.
- Segmentation `label` is often a room, block, split, or category placeholder;
  `label_seg` is the per-point target. Never substitute one for the other.
- Classification labels are one integer per sample. The selected setting's
  class count, not the maximum label observed in one split, defines the valid
  range. Keep label ids contiguous when they index class weights or logits.
- Converters commonly permute XYZ to XZY. Do not apply a second permutation or
  a second RGB/intensity normalization. Schema validation cannot prove the
  semantic coordinate orientation; record the converter contract.
- One-dimensional reconstruction indices (S3DIS/Semantic3D) and two-dimensional
  ScanNet pairs are different conventions. Do not mix them in one list.
- Preserve category/part/semantic mapping files next to the converted data and
  record the mapping used for every split.

## File-list generation and side effects

For already-converted files, a new flat list may be generated by a separately
approved read-only listing step. Use a new list name rather than overwriting an
existing list, then inspect it:

```bash
find /path/to/converted/train -type f -name '*.h5' -print | sort > /path/to/converted/train.generated.txt
python3 sub-skills/data-preparation/scripts/inspect_filelists.py \
  --list /path/to/converted/train.generated.txt --kind segmentation --check-h5
```

This example only lists paths and validates them; it does not run a converter.
For nested segmentation lists, place child lists in a dedicated list directory.
The top-level list contains child paths relative to itself; each child contains
HDF5 paths relative to that child. Do not mix HDF5 and child-list lines.

The downloader, archive extractors, Semantic3D shell helpers, dataset
converters, cache-marker writers, and PLY options are reference behavior only.
They can perform network access, extraction, moves, deletion of intermediate
folders, long-running HDF5 writes, randomization, huge storage allocation, or
large visualization output. Keep raw, converted, and visualization roots
separate, use a new destination, preserve logs and markers, and validate a tiny
sample before scaling up. Never infer completeness from a marker alone.

## Required handoff fields

A downstream workflow needs the explicit dataset root/list paths, task, split,
feature width, model point sample count, padded point width, class/part count,
label mapping, index convention and source bounds, and any unresolved cache or
acquisition limitation. A passing HDF5 check does not establish TensorFlow,
CUDA, or custom-op readiness.
