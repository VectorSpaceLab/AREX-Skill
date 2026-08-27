# Data formats and layout conventions

This reference captures the data-loader assumptions used by 3D-ResNets-PyTorch so a future agent does not need to reopen source files.

## Loader-level facts

- Supported dataset names in the repo data factory: `kinetics`, `activitynet`, `ucf101`, `hmdb51`, `mit`.
- Supported input types: `rgb`, `flow`.
- Supported file types: `jpg`, `hdf5`.
- `jpg` implies RGB only. The data factory asserts: `flow input is supported only when input type is hdf5`.
- RGB HDF5 uses a dataset named `video` containing encoded image bytes.
- Flow HDF5 uses datasets named `video_u` and `video_v`; the flow loader merges U, V, and a dummy third channel into an RGB-like image. Bundled scripts do not generate these datasets.
- The default JPEG image filename pattern is `image_%05d.jpg`, for example `image_00001.jpg`.

## Prepared video path conventions

### JPEG, non-ActivityNet

```text
VIDEO_ROOT/
  <label>/
    <video_id>/
      image_00001.jpg
      image_00002.jpg
      ...
```

For `VideoDataset`, the annotation key is `<video_id>`, the label is `annotations.label`, and the path is formed as `VIDEO_ROOT / label / video_id` unless the JSON entry explicitly includes `video_path`.

### HDF5, non-ActivityNet

```text
VIDEO_ROOT/
  <label>/
    <video_id>.hdf5
```

For RGB HDF5, each HDF5 file contains:

```text
/video  # length N, variable-length uint8 arrays containing encoded JPEG bytes
```

For flow HDF5 prepared outside these bundled scripts, each file must contain:

```text
/video_u
/video_v
```

### ActivityNet

The raw extractor expects flat ActivityNet videos:

```text
ACTIVITYNET_MP4_DIR/
  v_<id>.mp4
  v_<other_id>.mp4
```

The JPEG extractor writes:

```text
ACTIVITYNET_JPG_ROOT/
  v_<id>/
    image_00001.jpg
```

ActivityNet JSON database keys are commonly `<id>` without the `v_` prefix, while video files are commonly `v_<id>.mp4`. The fps augmentation command tries both keys.

ActivityNet annotations are temporal seconds before loading. The loader multiplies each annotation segment by the per-video `fps` field and converts to frame indices. Missing `fps` causes loader failure.

## Annotation JSON schema

### Generic VideoDataset JSON: Kinetics, UCF101, HMDB51, MIT

The generic JSON structure is:

```json
{
  "labels": ["class_a", "class_b"],
  "database": {
    "video_id": {
      "subset": "training",
      "annotations": {
        "label": "class_a",
        "segment": [1, 123]
      }
    }
  }
}
```

Fields:

- `labels`: ordered class names. The loader maps each class name to an integer by this order.
- `database`: maps video ids to metadata.
- `subset`: must match loader subset names: `training`, `validation`, or `testing`.
- `annotations.label`: required for training and validation entries; testing entries may omit labels.
- `annotations.segment`: half-open frame index range consumed with `range(start, end)`.
- Optional `video_path`: if present, `VideoDataset` uses it directly instead of composing `VIDEO_ROOT / label / video_id`. This is useful for HDF5 long-name fallbacks, but it should be an actual path valid from the runtime environment.

### Segment indexing rules

| Storage type | Segment written by bundled builder | Why |
| --- | --- | --- |
| JPEG frame directory | `[1, n_frames + 1]` | Frame names start at `image_00001.jpg`, and the loader asks for indices directly. |
| RGB HDF5 | `[0, n_frames]` | HDF5 dataset arrays are zero-indexed. |
| ActivityNet | time in seconds in source JSON; loader converts using `fps` | Each annotation segment is `floor(seconds * fps) + 1`, then clipped to available frames. |

Avoid mixing JPEG segments with HDF5 files: `[1, n + 1]` on HDF5 skips index 0 and can request index `n`, which is out of range.

## Dataset-specific inputs

### Kinetics

Raw videos:

```text
RAW_KINETICS/
  <label>/
    <youtube_id>_<time_start>_<time_end>.mp4
  test/                    # optional; used by some crawlers
    <video_id>.mp4
```

CSV inputs:

- Numbered names: `kinetics-400_train.csv`, `kinetics-400_val.csv`, optional `kinetics-400_test.csv` (also 600/700 variants).
- Unnumbered fallback names: `kinetics_train.csv`, `kinetics_val.csv`, optional `kinetics_test.csv`.
- Required columns: `youtube_id`, `time_start`, `time_end`, `label` for train/val; test can omit labels depending on source CSV.

Video id construction:

```text
<youtube_id>_<time_start as 6 digits>_<time_end as 6 digits>
```

For testing entries without labels, the bundled builder uses label `test` for path lookup.

### UCF101

Raw videos and prepared frames use class directories:

```text
RAW_UCF101/
  ApplyEyeMakeup/
    v_ApplyEyeMakeup_g01_c01.avi
```

Split directory:

```text
UCF101_SPLITS/
  classInd.txt
  trainlist01.txt
  testlist01.txt
  trainlist02.txt
  testlist02.txt
  trainlist03.txt
  testlist03.txt
```

`classInd.txt` contains integer ids and class names. Train/test list rows are paths like `ApplyEyeMakeup/v_ApplyEyeMakeup_g01_c01.avi`. The builder writes `ucf101_01.json`, `ucf101_02.json`, and `ucf101_03.json`.

### HMDB51

Raw videos and prepared frames use class directories. Split files are named like:

```text
brush_hair_test_split1.txt
brush_hair_test_split2.txt
brush_hair_test_split3.txt
```

Each row is `video_filename flag`, where:

- `1` means training.
- `2` means validation.
- `0` means ignored for that split.

The builder writes `hmdb51_1.json`, `hmdb51_2.json`, and `hmdb51_3.json`.

### Moments in Time

Annotation directory:

```text
MIT_ANNOTATION_DIR/
  moments_categories.txt
  trainingSet.csv
  validationSet.csv
  testingSet.csv      # optional
```

`moments_categories.txt` supplies labels from the first CSV column. Training and validation CSV rows use a path and label. Testing rows can contain only the video path/name.

### ActivityNet

Source JSON has ActivityNet-style fields:

```json
{
  "taxonomy": [
    {"nodeId": 1, "parentId": 0, "nodeName": "..."}
  ],
  "database": {
    "video_id_without_v_prefix": {
      "subset": "training",
      "annotations": [
        {"segment": [12.3, 20.0], "label": "class_name"}
      ],
      "fps": 29.97
    }
  }
}
```

ActivityNet labels are leaf nodes from `taxonomy`. The bundled fps command adds or updates `database[video_id].fps` by probing `.mp4` files. If raw files are named `v_<id>.mp4` and database keys are `<id>`, the command strips `v_` automatically.

## Frame-count and segment assumptions

- JSON generation counts only files named like `image_*.jpg`; hidden files and unrelated thumbnails do not count.
- For generic datasets, entries whose prepared path does not exist are skipped by the loader after JSON generation; using `--strict` in the bundled builder catches this earlier.
- Generic `VideoDataset` ignores entries where `segment[1] == 1`. That is why empty videos should not produce `[1, 1]` or `[0, 0]` in production annotations.
- ActivityNet discards activity clips with fewer than 8 frame indices.
- Very small synthetic generic JSONs can expose a loader progress-print bug because the loader computes `n_videos // 5`; for smoke tests, use at least five valid entries or patch the test harness.
