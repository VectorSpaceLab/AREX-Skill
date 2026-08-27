# Data Formats

## Purpose

Read this when you need the exact CULane or TuSimple file layout that the loaders and conversion script expect.

## CULane layout

The install instructions describe the CULane root as a directory containing at least:

- `driver_100_30frame`
- `driver_161_90frame`
- `driver_182_30frame`
- `driver_193_90frame`
- `driver_23_30frame`
- `driver_37_30frame`
- `laneseg_label_w16`
- `list`

Key list files used by the repo:

- `list/train_gt.txt`
- `list/test.txt`
- `list/test_split/test0_normal.txt`
- `list/test_split/test1_crowd.txt`
- `list/test_split/test2_hlight.txt`
- `list/test_split/test3_shadow.txt`
- `list/test_split/test4_noline.txt`
- `list/test_split/test5_arrow.txt`
- `list/test_split/test6_curve.txt`
- `list/test_split/test7_cross.txt`
- `list/test_split/test8_night.txt`

### Loader expectations

- `LaneTestDataset` reads image names from a list file and joins them to the dataset root.
- The test list for CULane strips a leading slash if one appears in the file.
- The training loader expects segmentation labels and image names paired in the list file.

## TuSimple layout

The install instructions describe the TuSimple root as a directory containing at least:

- `clips`
- `label_data_0313.json`
- `label_data_0531.json`
- `label_data_0601.json`
- `test_tasks_0627.json`
- `test_label.json`
- `readme.md`

The bundled converter also creates:

- `train_gt.txt`
- `test.txt`
- per-sample segmentation PNGs

### TuSimple JSON expectations

- The converter reads the standard TuSimple JSON lines format.
- Each record uses `raw_file`, `h_samples`, and `lanes`.
- Missing lane points are encoded as `-2` in the source annotations.

## Row anchors and class counts

- TuSimple row anchors: 56 rows.
- CULane row anchors: 18 rows.
- The dataset family controls `griding_num` and the class dimension used by the model.

## Output shapes used by the repo

- `LaneClsDataset` returns `(img, cls_label)` or `(img, cls_label, seg_label)` when auxiliary segmentation is enabled.
- `LaneTestDataset` returns `(img, name)`.
- TuSimple conversion writes segmentation masks with one label image per sample and a training list that includes the binary lane-presence flags.
