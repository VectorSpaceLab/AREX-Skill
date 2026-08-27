# Data-preparation workflows

These workflows use only the bundled scripts in this sub-skill. Replace paths with the user's dataset locations. After preparing data, validate/consume it with the downstream [training-and-inference sub-skill](../../training-and-inference/SKILL.md).

## Choose JPEG or HDF5 first

| Choice | Use when | Training/inference flags |
| --- | --- | --- |
| JPEG frame directories | You want the original README-style path, easy inspection, and RGB input only. | `--file_type jpg --input_type rgb` |
| RGB HDF5 files | You want fewer filesystem entries or need HDF5 input. | `--file_type hdf5 --input_type rgb` |
| Flow HDF5 | You already have optical flow packed as `video_u` and `video_v` HDF5 datasets. | `--file_type hdf5 --input_type flow` |

The bundled scripts extract RGB only. They do not compute optical flow.

## Extract RGB JPEG frames

General command:

```bash
python scripts/extract_video_frames.py RAW_VIDEO_DIR PREPARED_JPG_DIR DATASET --n_jobs 8 --size 240
```

Dataset controls:

- `DATASET=kinetics`, `mit`, or `activitynet` reads `.mp4` files.
- `DATASET=ucf101` or `hmdb51` reads `.avi` files.
- Non-ActivityNet datasets expect class subdirectories under `RAW_VIDEO_DIR` and write class subdirectories under `PREPARED_JPG_DIR`.
- ActivityNet expects a flat directory of `v_<id>.mp4` files and writes `PREPARED_JPG_DIR/v_<id>/image_00001.jpg`.

Optional controls:

```bash
# Keep original decoded frame rate.
python scripts/extract_video_frames.py RAW JPG kinetics --fps -1

# Resample decoded output to 30 fps and overwrite existing frames.
python scripts/extract_video_frames.py RAW JPG kinetics --fps 30 --overwrite

# Check planned paths without running ffmpeg.
python scripts/extract_video_frames.py RAW JPG ucf101 --dry-run
```

## Extract RGB HDF5 files

General command:

```bash
python scripts/extract_video_hdf5.py RAW_VIDEO_DIR PREPARED_HDF5_DIR DATASET --n_jobs 8 --size 240 --manifest PREPARED_HDF5_DIR/hdf5_manifest.json
```

Output conventions:

- Non-ActivityNet: `PREPARED_HDF5_DIR/<label>/<video_id>.hdf5`.
- ActivityNet: `PREPARED_HDF5_DIR/<video_stem>.hdf5`, usually `v_<id>.hdf5`.
- Each file contains variable-length JPEG bytes in dataset `video`.
- Long filenames are attempted in canonical form first. If the OS rejects a path as too long, the script writes a shortened `stem_hash.hdf5` filename and records the actual path in the optional manifest.

When a shortened HDF5 filename is used for Kinetics/UCF101/HMDB51/MIT, build annotations with `--path-map` and `--include-video-paths` so the standard `VideoDataset` loader can follow the actual file path:

```bash
python scripts/build_annotation_json.py kinetics KINETICS_CSV_DIR 700 PREPARED_HDF5_DIR hdf5 kinetics_hdf5.json \
  --path-map PREPARED_HDF5_DIR/hdf5_manifest.json --include-video-paths --strict --pretty
```

ActivityNet's specialized loader does not honor `video_path` entries in the same way as `VideoDataset`; for ActivityNet HDF5 with very long stems, prefer a shorter output root or canonical symlinks if the downstream loader expects canonical names.

## Build Kinetics JSON

Kinetics CSV directory should contain either `kinetics-<N>_train.csv`, `kinetics-<N>_val.csv`, optional `kinetics-<N>_test.csv`, or the unnumbered `kinetics_train.csv`, `kinetics_val.csv`, optional `kinetics_test.csv` variants. CSV rows need `youtube_id`, `time_start`, `time_end`, and `label` columns.

JPEG sequence:

```bash
python scripts/extract_video_frames.py RAW_KINETICS_MP4_DIR kinetics_jpg kinetics --n_jobs 8
python scripts/build_annotation_json.py kinetics KINETICS_CSV_DIR 700 kinetics_jpg jpg kinetics.json --strict --pretty
```

HDF5 sequence:

```bash
python scripts/extract_video_hdf5.py RAW_KINETICS_MP4_DIR kinetics_hdf5 kinetics --n_jobs 8 --manifest kinetics_hdf5/manifest.json
python scripts/build_annotation_json.py kinetics KINETICS_CSV_DIR 700 kinetics_hdf5 hdf5 kinetics_hdf5.json \
  --path-map kinetics_hdf5/manifest.json --include-video-paths --strict --pretty
```

The Kinetics builder sets segments from actual prepared data: JPEG entries get `[1, n_frames + 1]`; HDF5 entries get `[0, n_frames]`.

## UCF101 one-command-style sequence

UCF101 raw layout:

```text
RAW_UCF101/
  ApplyEyeMakeup/
    v_ApplyEyeMakeup_g01_c01.avi
  ...
UCF101_SPLITS/
  classInd.txt
  trainlist01.txt
  testlist01.txt
  trainlist02.txt
  testlist02.txt
  trainlist03.txt
  testlist03.txt
```

Preparation sequence:

```bash
python scripts/extract_video_frames.py RAW_UCF101 ucf101_jpg ucf101 --n_jobs 8 --size 240
python scripts/build_annotation_json.py ucf101 UCF101_SPLITS ucf101_jpg annotations --strict --pretty
```

This writes `annotations/ucf101_01.json`, `ucf101_02.json`, and `ucf101_03.json`. Use the selected split's JSON with downstream flags similar to:

```bash
--dataset ucf101 --video_path ucf101_jpg --annotation_path annotations/ucf101_01.json --file_type jpg --input_type rgb
```

Do **not** set `--input_type flow` for this JPEG workflow. The repository asserts that flow requires HDF5, and the bundled frame extractor writes RGB JPEGs only.

If the user insists on HDF5 for UCF101, convert to HDF5 and request HDF5 annotation segments:

```bash
python scripts/extract_video_hdf5.py RAW_UCF101 ucf101_hdf5 ucf101 --n_jobs 8 --manifest ucf101_hdf5/manifest.json
python scripts/build_annotation_json.py ucf101 UCF101_SPLITS ucf101_hdf5 annotations_hdf5 \
  --video-type hdf5 --path-map ucf101_hdf5/manifest.json --include-video-paths --strict --pretty
```

Then consume with `--file_type hdf5 --input_type rgb`, not flow.

## HMDB51 sequence

HMDB51 raw layout mirrors labels as directories and split text files are named like `brush_hair_test_split1.txt`:

```bash
python scripts/extract_video_frames.py RAW_HMDB51 hmdb51_jpg hmdb51 --n_jobs 8
python scripts/build_annotation_json.py hmdb51 HMDB51_SPLITS hmdb51_jpg annotations --strict --pretty
```

This writes `hmdb51_1.json`, `hmdb51_2.json`, and `hmdb51_3.json`. HDF5 is supported by the bundled builder via `--video-type hdf5`, but the original repository utility only generated JPEG annotations.

## Moments in Time sequence

Moments in Time annotation directory should contain `moments_categories.txt`, `trainingSet.csv`, `validationSet.csv`, and optional `testingSet.csv`.

```bash
python scripts/extract_video_frames.py RAW_MIT_MP4_DIR mit_jpg mit --n_jobs 8
python scripts/build_annotation_json.py mit MIT_ANNOTATION_DIR mit_jpg mit.json --strict --pretty
```

For HDF5:

```bash
python scripts/extract_video_hdf5.py RAW_MIT_MP4_DIR mit_hdf5 mit --n_jobs 8 --manifest mit_hdf5/manifest.json
python scripts/build_annotation_json.py mit MIT_ANNOTATION_DIR mit_hdf5 mit_hdf5.json \
  --video-type hdf5 --path-map mit_hdf5/manifest.json --include-video-paths --strict --pretty
```

## ActivityNet existing JSON plus fps

ActivityNet preparation starts from an existing ActivityNet-style JSON with top-level `taxonomy` and `database`. Each database entry has `subset` and a list of temporal annotations in seconds. The repository loader requires an `fps` field on every video entry before it can convert those time segments to frame indices.

JPEG frame workflow:

```bash
python scripts/extract_video_frames.py ACTIVITYNET_MP4_DIR activitynet_jpg activitynet --n_jobs 8
python scripts/build_annotation_json.py activitynet-add-fps ACTIVITYNET_MP4_DIR activitynet.json activitynet_with_fps.json --strict --pretty
```

HDF5 extraction with a manifest:

```bash
python scripts/extract_video_hdf5.py ACTIVITYNET_MP4_DIR activitynet_hdf5 activitynet --n_jobs 8 \
  --manifest activitynet_hdf5/manifest.json
python scripts/build_annotation_json.py activitynet-add-fps ACTIVITYNET_MP4_DIR activitynet.json activitynet_with_fps.json --strict --pretty
```

For long ActivityNet video paths:

1. The HDF5 extractor writes frames through a short temporary directory, then tries the canonical `<video_stem>.hdf5` destination.
2. If the canonical filename is too long, it writes a shortened hash-suffixed HDF5 file and records that in the manifest.
3. Downstream ActivityNet consumption should be validated carefully because the repository's ActivityNet dataset path logic is stricter than the generic `VideoDataset` `video_path` override. Prefer shortening the destination root/stem before training if canonical names are required.

## Layout-check workflow before training

Before handing off to training/inference:

```bash
# Show script-level expectations.
python scripts/build_annotation_json.py -h

# Fail early on missing files while building JSON.
python scripts/build_annotation_json.py kinetics KINETICS_CSV_DIR 700 kinetics_jpg jpg kinetics.json --strict
```

Then hand the user to [training-and-inference](../../training-and-inference/SKILL.md) to run a loader smoke check or a tiny `scripts/run_main.py` command with the matching `--dataset`, `--video_path`, `--annotation_path`, `--file_type`, and `--input_type` flags.
