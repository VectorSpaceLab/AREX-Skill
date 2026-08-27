# ScanNet data formats and label contracts

This reference is self-contained for the PointNet2 ScanNet semantic scene workflow. It describes the data that the legacy trainer and dataset loaders expect, plus the raw preprocessing artifacts that can produce that data.

## Semantic class ids

The repository uses 21 semantic ids. Id `0` is background/unknown and is excluded from accuracy metrics.

| id | class name |
|---:|---|
| 0 | unannotated |
| 1 | wall |
| 2 | floor |
| 3 | chair |
| 4 | table |
| 5 | desk |
| 6 | bed |
| 7 | bookshelf |
| 8 | sofa |
| 9 | sink |
| 10 | bathtub |
| 11 | toilet |
| 12 | curtain |
| 13 | counter |
| 14 | door |
| 15 | window |
| 16 | shower curtain |
| 17 | refridgerator |
| 18 | picture |
| 19 | cabinet |
| 20 | otherfurniture |

The spelling `refridgerator` is the spelling used by the source label list and should be preserved when matching legacy artifacts.

## `scannet_data_pointnet2` pickle layout

The trainer looks for a data root named like:

```text
data/scannet_data_pointnet2/
  scannet_train.pickle
  scannet_test.pickle
```

Each split pickle must contain **two pickle objects in sequence**:

1. `scene_points_list`: list-like object with one NumPy-compatible array per scene.
   - Required shape per scene: `N x 3`.
   - Columns are XYZ only. The semantic segmentation model placeholder is `(batch_size, num_point, 3)`, so RGB or instance columns inside the training pickle will break batching.
   - `N` may be smaller than `num_point` because the loader samples with replacement, but each scene must have at least one point.
2. `semantic_labels_list`: list-like object with one 1-D integer label array per scene.
   - Required shape per scene: `N`.
   - Length must match the corresponding points array.
   - Values must be integer-like ids in `[0, 20]` unless the workflow has deliberately changed `NUM_CLASSES` and retrained the model.

Training split label weights are computed from a histogram over `range(22)` and then transformed as `1 / log(1.2 + class_frequency)`. Test split sample weights are all ones. Any unexpected label id can therefore fail either the histogram/weight computation or later indexing.

Use the bundled validator before training:

```bash
python3 scripts/validate_scannet_layout.py data/scannet_data_pointnet2 --splits train test
```

For a tiny self-check independent of the original checkout:

```bash
python3 scripts/smoke_scannet_loader.py --make-fixture <fixture-dir> --npoints 16
python3 scripts/validate_scannet_layout.py <fixture-dir> --splits train test
```

## Random block loader behavior

`ScannetDataset` samples one block from a scene on each `__getitem__` call:

- Chooses a random point as a candidate block center.
- Uses a `1.5m x 1.5m` XY window and the full scene Z extent, with a slightly larger `0.2m` margin for candidate points.
- Tries up to 10 random centers until both conditions hold:
  - at least 70% of candidate labels are greater than `0`;
  - occupied cells cover at least 2% of a `31 x 31 x 62` coarse occupancy grid.
- Samples `num_point` points with replacement.
- Applies the stricter inner block mask to sample weights, so points from the margin can have zero weight.

Training then applies point dropout: a random ratio in `[0, 0.875]` is chosen, dropped points are replaced by the first point in the block, and their sample weights are zeroed.

## Whole-scene loader behavior

`ScannetDatasetWholeScene` tiles a full scene into XY cells:

- Cell size is `1.5m x 1.5m`; Z spans the full scene height.
- Candidate points use the same `0.2m` margin.
- A tile is kept only if the strict inner mask covers at least 1% of its sampled points.
- Each kept tile yields one `num_point x 3` sample and matching labels/weights.

The trainer's whole-scene evaluator concatenates tile batches across scenes until it has `batch_size` tiles. If a single scene yields more than `batch_size` tiles, overflow is carried into the next model call. This is correct for the legacy script but can surprise users because memory depends on both `num_point` and the number of tiles produced by large scenes.

## Raw ScanNet preprocessing inputs

The reference preprocessing recipe expects an external raw ScanNet download laid out with one folder per scene. For a scene such as `scene0001_01`, the collector expects:

```text
<raw-scan-root>/scene0001_01/
  scene0001_01_vh_clean_2.0.010000.segs.json
  scene0001_01_vh_clean_2.ply
  scene0001_01.aggregation.json
```

It also expects a `scannet_all.txt` scene-list file. For each scene, the collector:

1. reads over-segmentation ids from `*.segs.json`;
2. reads XYZRGBA points from `*_vh_clean_2.ply`;
3. reads instance segment groups and raw labels from `*.aggregation.json`;
4. maps raw labels through the TSV-derived raw-to-ScanNet label map;
5. writes `scannet_scenes/<scene>.npy`.

The generated `.npy` scene file has shape `N x 8`:

| columns | meaning |
|---|---|
| `0:3` | XYZ |
| `3:6` | RGB |
| `6` | instance id assigned by the collector |
| `7` | semantic class id from the 21-class table |

These `.npy` files are not the same as the trainer pickles. The trainer pickles should contain XYZ arrays and separate 1-D semantic label arrays.

## Label-table handling

The V1 preprocessing utility reads `scannet-labels.combined.tsv` with tab-separated columns and maps:

- raw class name from column `0` (`category` in the bundled V1 table);
- NYU40 semantic name from column `6` (`nyu40class` in the bundled V1 table).

If the NYU40 name is not one of the 21 class names, the raw label maps to `unannotated`.

The repository note says that ScanNetV2 requires changing the TSV file to `scannetv2-labels.combined.tsv` **and** updating the raw-class and NYU40-name columns because they are shifted by one compared with V1. Do not assume the V1 `(0, 6)` columns for V2. Use explicit validator overrides after checking the V2 header, for example:

```bash
python3 scripts/validate_scannet_layout.py --label-tsv scannetv2-labels.combined.tsv --raw-column 1 --nyu40-column 7
```

If the validator reports that no NYU40 names match the 21-class table, the likely cause is a V1/V2 column mismatch rather than a model problem.

## Demo output contract

The reference visualization demo expects `scannet_scenes/scene0001_01.npy` and writes three files under `demo_output/`:

```text
demo_output/
  scene.obj
  scene_instance.obj
  scene_semantic.obj
```

The demo output check is intentionally separate from raw-data checks: a user can have valid raw scene folders but no generated demo output, or a stale demo output without the raw ScanNet download.
