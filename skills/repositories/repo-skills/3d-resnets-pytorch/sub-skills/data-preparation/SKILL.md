---
name: "data-preparation"
description: "Prepare raw videos and annotations for the 3D-ResNets-PyTorch
  dataset loaders."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Data preparation

Use this sub-skill when a user needs raw videos converted into the directory and JSON formats consumed by 3D-ResNets-PyTorch. For downstream training, validation, or inference flags after data is prepared, route to [training-and-inference](../training-and-inference/SKILL.md); for top-level routing, return to the [root skill](../../SKILL.md).

## Fast routing

| User needs | Open/use |
| --- | --- |
| Extract RGB JPEG frames from Kinetics, ActivityNet, UCF101, HMDB51, or Moments in Time videos | [`scripts/extract_video_frames.py`](scripts/extract_video_frames.py), then [workflows](references/workflows.md#extract-rgb-jpeg-frames) |
| Convert raw RGB videos to HDF5 files | [`scripts/extract_video_hdf5.py`](scripts/extract_video_hdf5.py), then [workflows](references/workflows.md#extract-rgb-hdf5-files) |
| Build Kinetics/UCF101/HMDB51/MIT annotation JSON files | [`scripts/build_annotation_json.py`](scripts/build_annotation_json.py), then [data formats](references/data-formats.md#annotation-json-schema) |
| Add missing ActivityNet `fps` fields | `build_annotation_json.py activitynet-add-fps`, then [ActivityNet workflow](references/workflows.md#activitynet-existing-json-plus-fps) |
| Diagnose missing videos, empty loaders, `flow`/`jpg` assertions, or long HDF5 names | [troubleshooting](references/troubleshooting.md) |

## Core rules to preserve

- Prepared JPEG layout is normally `<video_root>/<label>/<video_id>/image_00001.jpg`; ActivityNet raw extraction is flat and produces `<video_root>/v_<id>/image_00001.jpg`.
- Prepared RGB HDF5 layout is normally `<video_root>/<label>/<video_id>.hdf5` with a variable-length byte dataset named `video`. The bundled HDF5 extractor does **not** create optical-flow datasets.
- `--file_type jpg` must be paired with `--input_type rgb`. The repository asserts that `flow` is supported only when `--file_type hdf5`, and flow HDF5 must contain `video_u` and `video_v` datasets prepared elsewhere.
- For frame-directory annotations, segments are one-based half-open ranges such as `[1, n_frames + 1]`. For RGB HDF5 annotations, use zero-based half-open ranges `[0, n_frames]`.
- ActivityNet JSON must have per-video `fps` values before the ActivityNet loader can convert time segments to frame indices.

## Bundled scripts

Run scripts from this sub-skill directory or call them by path:

```bash
python scripts/extract_video_frames.py -h
python scripts/extract_video_hdf5.py -h
python scripts/build_annotation_json.py -h
python scripts/build_annotation_json.py kinetics -h
python scripts/build_annotation_json.py activitynet-add-fps -h
```

The scripts are self-contained adaptations of the repository utilities; they do not import from or link to the source checkout.
