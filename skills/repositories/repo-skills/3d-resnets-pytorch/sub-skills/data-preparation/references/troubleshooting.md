# Data-preparation troubleshooting

Use this reference when a prepared dataset cannot be generated or the downstream loader cannot find frames/HDF5 files.

## Missing FFmpeg or FFprobe

Symptoms:

- `Missing required tool(s) on PATH: ffmpeg, ffprobe`
- `ffprobe failed ...`
- FPS augmentation writes no `fps` fields.

Checks:

```bash
which ffmpeg
which ffprobe
ffmpeg -version
ffprobe -version
```

Fix:

- Install FFmpeg with FFprobe included, or fix `PATH` so both commands are visible to the Python process.
- Re-run the bundled script with `--dry-run` first if you are unsure about input/output layout.

## Dataset directory layout mismatches

### Kinetics or Moments in Time

Expected raw input for extraction is class subdirectories containing `.mp4` files. Expected prepared JPEG/HDF5 layout is class subdirectories under the prepared root.

Common mistakes:

- Pointing the extractor at a directory of CSV files instead of videos.
- Flattening all Kinetics videos into one directory; the generic loader later expects `VIDEO_ROOT / label / video_id` unless `video_path` overrides are used.
- Using unpadded Kinetics ids. JSON ids are constructed as `<youtube_id>_<time_start:06d>_<time_end:06d>`.
- Supplying `kinetics_train.csv` while the script is looking for numbered names. The bundled builder accepts both numbered (`kinetics-700_train.csv`) and unnumbered (`kinetics_train.csv`) variants.

### UCF101

Expected split files:

```text
classInd.txt
trainlist01.txt testlist01.txt
trainlist02.txt testlist02.txt
trainlist03.txt testlist03.txt
```

Expected list rows look like `ApplyEyeMakeup/v_ApplyEyeMakeup_g01_c01.avi`. If rows do not contain `class/video.avi`, label extraction will fail.

### HMDB51

Expected split files are one per class and split, for example `brush_hair_test_split1.txt`. The class label is parsed from the filename before `_test_split`. Row flags mean `1=training`, `2=validation`, `0=ignore`.

### ActivityNet

Expected raw videos are usually flat `v_<id>.mp4` files. Existing JSON database keys are usually `<id>` without `v_`. The fps augmenter tries both forms. Use `--strict` to fail if any `.mp4` has no matching database key.

## JPEG vs HDF5 and RGB vs flow constraints

Symptoms:

- Assertion like `flow input is supported only when input type is hdf5`.
- Loader looks for HDF5 datasets named `video_u` or `video_v` and fails.
- HDF5 loader returns fewer frames than expected.

Rules:

- JPEG workflows are RGB only: use downstream `--file_type jpg --input_type rgb`.
- Bundled HDF5 extraction is RGB only: use `--file_type hdf5 --input_type rgb`.
- `--input_type flow` requires HDF5 files prepared outside this sub-skill with datasets `video_u` and `video_v`; the bundled scripts do not compute optical flow.
- Do not reuse JPEG-style segments for HDF5 annotations. HDF5 segments should be `[0, n_frames]`; JPEG segments should be `[1, n_frames + 1]`.

## ActivityNet fps augmentation

Symptoms:

- KeyError or missing-field error for `fps` in ActivityNet loading.
- ActivityNet clips produce empty or wrong frame ranges.

Fix:

```bash
python scripts/build_annotation_json.py activitynet-add-fps ACTIVITYNET_MP4_DIR activitynet.json activitynet_with_fps.json --strict --pretty
```

The command probes each `.mp4` with FFprobe and writes `database[key].fps`. If raw file names are `v_<id>.mp4`, it first tries database key `v_<id>` and then `<id>`.

Remember that ActivityNet source annotation segments are in seconds. The loader converts them to frames with `floor(seconds * fps) + 1`, clips the end to the available frame count, and drops clips shorter than 8 frames.

## Long HDF5 output paths

Symptoms:

- `OSError: errno = 36`
- `File name too long`
- HDF5 extraction succeeds but the downstream loader cannot find the file.

Bundled extractor behavior:

1. Frames are decoded through a short temporary directory to avoid long temporary frame paths.
2. The script tries to write the canonical destination `<video_id>.hdf5`.
3. If the OS rejects the filename as too long, the script writes a shortened hash-suffixed filename such as `<truncated_stem>_<hash>.hdf5`.
4. If `--manifest` is set, the manifest records `video_id`, label, canonical path, actual path, and whether fallback was used.

For Kinetics/UCF101/HMDB51/MIT, pair the manifest with annotation building:

```bash
python scripts/build_annotation_json.py kinetics KINETICS_CSV_DIR 700 HDF5_ROOT hdf5 kinetics.json \
  --path-map HDF5_ROOT/manifest.json --include-video-paths --strict
```

For ActivityNet, validate carefully after any fallback. Its specialized loader does not use generic per-entry `video_path` in the same way. Prefer shortening the destination root or creating canonical symlinks if the downstream loader expects canonical names.

## Frame count and segment indexing errors

Symptoms:

- JSON builds, but loader silently drops samples.
- Loader raises when trying to open `image_00000.jpg` or an out-of-range HDF5 index.
- Validation/inference multi-clip loading returns short clips.

Checks:

```bash
# JPEG frame count for one video.
find VIDEO_ROOT/LABEL/VIDEO_ID -maxdepth 1 -name 'image_*.jpg' | wc -l

# HDF5 RGB frame count for one video.
python - <<'PY'
import h5py
with h5py.File('VIDEO_ROOT/LABEL/VIDEO_ID.hdf5', 'r') as f:
    print(len(f['video']))
PY
```

Fixes:

- Rebuild annotations with `--strict` so missing or empty prepared videos fail early.
- For JPEG, confirm the first frame is `image_00001.jpg` and the JSON segment starts at 1.
- For HDF5, confirm the JSON segment starts at 0 and ends at the dataset length.
- For ActivityNet, confirm `fps` values are present and realistic; bad fps shifts every segment.

## Downstream handoff checklist

Before handing off to training/inference, record:

- Dataset name: `kinetics`, `activitynet`, `ucf101`, `hmdb51`, or `mit`.
- Prepared storage: `jpg` or `hdf5`.
- Input type: `rgb` unless the user independently prepared flow HDF5.
- Video root and annotation JSON path.
- For split datasets, selected split JSON (`ucf101_01.json`, `hmdb51_1.json`, etc.).
- Any HDF5 manifest/path-map use or ActivityNet fps augmentation performed.
