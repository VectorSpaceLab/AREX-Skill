# API reference

This sub-skill focuses on the PyTorch path that DeepLabCut uses for training, evaluation, image/video inference, and export.

## User-facing entry points

| Entry point | What it does | Key PyTorch controls | Typical outputs |
| --- | --- | --- | --- |
| `deeplabcut.train_network(...)` | Train or resume a shuffle with the PyTorch engine. | `epochs`, `save_epochs`, `device`, `snapshot_path`, `detector_path`, `batch_size`, `detector_batch_size`, `detector_epochs`, `detector_save_epochs`, `pose_threshold`, `pytorch_cfg_updates` | Snapshots, training log, updated `pytorch_config` |
| `deeplabcut.evaluate_network(...)` | Evaluate one or more shuffles and snapshots. | `shuffles`, `plotting`, `comparison_bodyparts`, `pcutoff`, `torch_kwargs` | Evaluation `.h5` / `.csv`, optional labeled figures, per-keypoint scores |
| `deeplabcut.analyze_images(...)` | Run PyTorch inference on image files or folders. | `frame_type`, `destfolder`, `snapshot_index`, `detector_snapshot_index`, `device`, `max_individuals`, `save_as_csv`, `plotting`, `pcutoff`, `bbox_pcutoff`, `plot_skeleton`, `torch_kwargs` | Image predictions `.h5` / `.csv`, optional labeled images |
| `deeplabcut.analyze_videos(...)` | Run PyTorch inference on videos. | `videos`, `save_as_csv`, `destfolder`, `batch_size`, `dynamic`, `auto_track`, `n_tracks`, `animal_names`, `identity_only`, `use_shelve`, `overwrite`, `cropping`, `inference_cfg` | Full prediction pickle, metadata pickle, analyzed `.h5` / `.csv`, optional assemblies and tracking outputs |
| `deeplabcut.export_model(...)` | Export a PyTorch model for reuse or live inference. | `snapshotindex`, `detector_snapshot_index`, `overwrite`, `wipepaths`, `without_detector`, `modelprefix` | `exported-models-pytorch/.../*.pt` |
| `return_train_network_path(...)` | Locate the PyTorch train/test config files and snapshot folder. | `shuffle`, `trainingsetindex`, `modelprefix` | Training config path, test config path, snapshot folder |

## PyTorch-specific notes

- `train_network` uses `device` for the torch device and `pytorch_cfg_updates` for dotpath config edits.
- `snapshot_path` resumes pose training from a checkpoint; `detector_path` resumes the detector branch for top-down models.
- `detector_epochs=0` keeps the detector from training.
- `pose_threshold` is only for memory replay / pseudo-label filtering. It is not the same as analysis `pcutoff`.
- `evaluate_network(..., **torch_kwargs)` passes PyTorch-only overrides through the routing wrapper. Use it for snapshot selection and other engine-specific options.
- `analyze_images` and `analyze_videos` are the inference entry points. `analyze_videos` also accepts `inference_cfg` for inference-time runner choices.
- `export_model` bundles the chosen pose snapshot and, for top-down models, the detector snapshot unless `without_detector=True`.

## Output landmarks

- Training writes snapshots under the shuffle's train folder.
- Evaluation writes to an evaluation-results folder and can also plot predictions.
- Image inference writes a scorer-named HDF/CSV file plus optional labeled image folders.
- Video inference writes a scorer-named full prediction pickle and metadata, and may also write tracked or assembled outputs for multi-animal projects.
- Export writes a relocation-friendly `.pt` bundle for live inference or reuse.

## Notes on top-down and CTD cases

- Top-down analysis and evaluation need a detector snapshot unless the model path explicitly avoids detector use.
- Conditional top-down models need `inference.conditions` to resolve correctly.
- File-path conditions are evaluation-only; live image/video inference must use a model/shuffle-based condition provider.
