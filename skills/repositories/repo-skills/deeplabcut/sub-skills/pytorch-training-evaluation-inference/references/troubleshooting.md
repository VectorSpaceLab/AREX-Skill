# Troubleshooting

This guide covers the PyTorch training, evaluation, inference, and export path.

| Symptom | Likely cause | What to do | Route if needed |
| --- | --- | --- | --- |
| Training ignores your override | `pytorch_cfg_updates` used the wrong dotpath or the wrong value type | Inspect the generated config, then update the exact nested key such as `train_settings.batch_size` or `runner.device` | Stay here |
| Training resumes from an unexpected checkpoint | `snapshot_path` or `detector_path` points at the wrong snapshot, or the shuffle/model folder is not the one you expected | Re-check the snapshot folder and the chosen shuffle before retraining | Stay here |
| The run uses CPU when you expected GPU | The device selection is still `auto`, the hardware is not visible, or the config override points to `cpu` | Choose `device` deliberately and keep `runner.device` consistent with it | Stay here |
| Top-down training or inference cannot find a detector snapshot | The top-down detector branch was never trained, or the wrong detector index was selected | Train the detector branch, point to the detector snapshot explicitly, or export without the detector only when that is the intended outcome | Stay here |
| Evaluation fails with an empty bodypart set | `comparison_bodyparts` removed every selectable bodypart, including unique bodyparts | Use `None` or `all`, or pick a subset that still leaves at least one valid bodypart | Stay here |
| Evaluation fails because the `pcutoff` shape is wrong | The confidence cutoff does not match the number of bodyparts plus unique bodyparts | Use a single scalar, a list with the correct length, or a dict keyed by bodypart name | Stay here |
| Image or video inference produces no files | The image filter missed every file, the snapshot choice was wrong, or the output folder is not what you expected | Re-check the input list, the file extension filter, the snapshot index, and the destination folder | Stay here |
| Video inference writes raw predictions but no final multi-animal tracks | `auto_track` was disabled, or the analysis was intentionally left at the detection stage | Run the multi-animal tracklet and stitching steps in the tracking sub-skill | [multi-animal-tracking](../../multi-animal-tracking/SKILL.md) |
| `use_shelve` and `save_as_df` seem to conflict | Shelf-backed output and DataFrame export cannot be used the same way for every project mode | Choose one output style and keep it consistent across runs | Stay here |
| `animal_names` and `n_tracks` disagree | The names list length does not match the requested track count | Make the two settings consistent, or let `n_tracks` come from the project metadata | Stay here |
| Dynamic cropping does not do anything | Dynamic crop is for bottom-up inference; top-down uses a different cropper path | Use the top-down dynamic cropper for top-down single-animal cases | Stay here |
| CTD analysis complains about conditions | Live inference expects a model/shuffle-based condition provider, while file-path conditions are evaluation-only | Rebuild the conditions choice so it is valid for live analysis | Stay here |
| Export fails for a top-down model | The export needs a detector snapshot unless you explicitly request a detector-free export | Export the detector too, or set `without_detector=True` on purpose | Stay here |
| Video analysis seems incomplete or corrupt | The video metadata and actual frames disagree | Re-encode the source video or use the robust frame-count option when appropriate | Stay here |
| The wrapper routes to TensorFlow instead of PyTorch | The project engine or shuffle metadata still points to TensorFlow | Switch the project to PyTorch or use the root compatibility layer for TensorFlow-specific work | Root compatibility |

## Distinguish these thresholds

- `pose_threshold` is used for memory replay / pseudo-label filtering during training.
- `pcutoff` is used during evaluation and plotting.
- `bbox_pcutoff` is used for top-down bounding boxes during plotting and inference.

## Common recovery checks

- Re-run the config inspector and verify the sections are present.
- Confirm the selected snapshot exists before starting a long job.
- Confirm the project engine is really PyTorch before routing the workflow here.
- If the issue is actually about labeled video rendering, filtering, or 3D outputs, hand off to the post-processing sub-skill.
