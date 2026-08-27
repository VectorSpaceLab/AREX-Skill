# Dataset Formats

## HDF5 demonstration datasets

Mimic and teleoperation workflows store demonstrations in HDF5 files. The common top-level layout is:

- `data/demo_<id>/actions`
- `data/demo_<id>/obs/...`
- `data/demo_<id>` attributes such as `num_samples`

Common observation keys seen in the source workflows include:

- `eef_pos`
- `eef_quat`
- `gripper_pos`
- `table_cam`
- `wrist_cam`
- `table_cam_depth`
- `table_cam_segmentation`
- `table_cam_normals`
- `table_cam_shaded_segmentation`

Not every task exports every key. Treat absent keys as a task-specific schema difference, not necessarily an error.

## MP4 export naming

When converting visually augmented videos back into HDF5 form, the video files must preserve the original demo ID in the filename. A safe pattern is:

- `demo_<demo_id>_<camera_or_variant>.mp4`

The demo ID is used to pair the augmented video with the original HDF5 episode.

## Annotation signal conventions

SkillGen-style workflows rely on subtask signals rather than only the final success flag. The relevant logical fields are:

- `subtask_term_signal`
- `subtask_start_signal`
- `object_ref`

A subtask is a contiguous demo segment delimited by signal transitions. When start signals are required, the dataset must provide them explicitly.

## Repository-specific workflow assumptions

- The source data-generation workflows assume the dataset file exists before annotation or augmentation starts.
- A visual-augmentation run should preserve the non-visual state data while replacing the video frames or exporting them to intermediate files.
- Merge operations should preserve the environment metadata from the first source dataset. Use the bundled `scripts/merge_hdf5_datasets.py` helper for the simple Isaac Lab-style `data/demo_*` merge case.
