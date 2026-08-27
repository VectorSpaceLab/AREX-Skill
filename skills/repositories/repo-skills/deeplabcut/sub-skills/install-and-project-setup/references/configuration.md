# Configuration and layout

## Core file
`config.yaml` is the project state file. It belongs at the project root.

Important behavior:
- `Task`, `scorer`, and `date` identify the project and should not be edited after creation.
- `project_path` should point to the project root.
- If the project is moved after creation, `project_path` can become stale.
- The bundled summary script reports mismatches without changing files.

## Standard project fields
These are the most important project-level fields for a standard project:

- `Task`: short project name
- `scorer`: scorer or experimenter label
- `date`: creation date stamp
- `project_path`: root directory for the project
- `engine`: default engine for the project; DeepLabCut 3.x defaults to PyTorch
- `video_sets`: mapping from each video path to its crop metadata
- `TrainingFraction`: train/test split fractions; the default project template starts with `[0.95]`
- `bodyparts`: list of body parts to track in a standard project
- `skeleton`: optional list of body-part pairs used for plotting
- `skeleton_color`, `pcutoff`, `dotsize`, `alphavalue`, `colormap`: visualization defaults
- `cropping`, `x1`, `x2`, `y1`, `y2`: crop controls used by later analysis steps
- `snapshotindex`, `detector_snapshotindex`, `batch_size`, `detector_batch_size`: later workflow controls

The `video_sets` mapping stores the video path as the key and a small dictionary as the value. The common entry is a `crop` string.

## Multi-animal fields
A multi-animal project uses additional fields:

- `multianimalproject`: marks the project as multi-animal
- `individuals`: the identity labels used in annotation and later tracking
- `multianimalbodyparts`: body parts shared by all individuals
- `uniquebodyparts`: landmarks or objects that appear only once per frame
- `bodyparts`: becomes the sentinel `MULTI!` in the template rather than a normal list
- `identity`: whether individuals should be labeled consistently across frames
- `default_net_type`, `default_augmenter`, `default_track_method`: downstream defaults chosen at project creation time

Practical rules:
- Use `individuals` for the actual animal names or IDs.
- Set `identity=True` only when the same animal can be recognized consistently.
- Keep names free of spaces.
- Replace placeholder identity names before labeling.

## 3D fields
A 3D project uses a different group of configuration keys:

- `num_cameras`: number of camera views used for the 3D project
- `camera_names`: stable camera labels that should not be changed after setup
- `scorername_3d`: prefix used for 3D outputs
- `config_file_camera-#`: reference to the 2D config for each camera
- `shuffle_camera-#`: shuffle index for each camera
- `trainingsetindex_camera-#`: training-set index for each camera
- `skeleton`, `skeleton_color`, `pcutoff`, `dotsize`, `alphaValue`, `markerType`, `markerColor`: 3D plotting defaults

The 3D config also expects a project skeleton with calibration folders:
- `calibration_images/`
- `camera_matrix/`
- `corners/`
- `undistortion/`

## Project layout over time
A fresh project should be treated as a growing tree. The common top-level folders are:

```text
project/
  config.yaml
  videos/
  labeled-data/
  training-datasets/
  dlc-models/
  dlc-models-pytorch/
```

And a 3D project adds:

```text
project-3d/
  config.yaml
  calibration_images/
  camera_matrix/
  corners/
  undistortion/
```

Not every folder appears at the same moment. The engine-specific model folders usually appear as the matching workflow steps create their first outputs.

## What the summary script reports
The bundled `scripts/summarize_dlc_project.py` script reports a JSON summary of:
- the config fields that matter for setup
- the stored `project_path` versus the actual project root
- which top-level folders are present
- a bounded sample of `video_sets`
- 3D metadata when present

It does not edit the project.
