# PyTorch workflows

This guide focuses on the DeepLabCut 3.x PyTorch path for training, evaluation, image/video inference, and export.

## 1. Choose the path first

- If you still need labeled frames, frame extraction, or training-dataset creation, route upstream first.
- If you need tracklets, identity stitching, or re-identification after analysis, route downstream after `analyze_videos`.
- If you need SuperAnimal pretrained inference or adaptation, use the model-zoo sub-skill instead of training from scratch.
- If you need filtered predictions, labeled-video rendering, or 3D outputs, route to the post-processing sub-skill after inference.

## 2. Minimal bottom-up training loop

1. Confirm the project uses the PyTorch engine.
2. Inspect the generated PyTorch config if you need to check or edit it.
3. Train with the batch size, epoch budget, and device you actually want.
4. Evaluate one or more shuffles or snapshots.
5. Run image or video inference on the selected media.
6. Hand off the analyzed scorer files for labeled-video rendering if you need visual review.

Suggested choices:

- `epochs` for how long to train
- `save_epochs` for checkpoint cadence
- `device` for CPU, CUDA, or MPS selection
- `pytorch_cfg_updates` for one-off config overrides

## 3. Top-down training loop

Use this when the project needs a detector plus a pose head.

1. Choose the detector architecture.
2. Set detector-specific epochs, batch size, and save cadence if the detector should train.
3. Provide `snapshot_path` and `detector_path` when resuming from checkpoints.
4. Keep `runner.device` aligned between pose and detector branches.
5. Evaluate the detector-supported pose model before running video inference.

Useful choices:

- `detector_epochs=0` when you want to keep the detector frozen
- `detector_batch_size` when the detector needs a different memory budget
- `without_detector=True` only when exporting a detector-free bundle on purpose

## 4. Image inference workflow

Use this when you need labeled frame-level outputs rather than a full video pass.

1. Provide one image, a list of images, or a folder.
2. Use `frame_type` if you only want one file extension.
3. Set `destfolder` when you want a dedicated output location.
4. Use `plotting=True` for a quick visual check.
5. Narrow `pcutoff` or `bbox_pcutoff` only when you understand the score threshold you want.

Outputs to expect:

- image prediction tables
- optional labeled image folders
- optional CSV alongside the HDF file

## 5. Video inference workflow

Use this for the standard pose-estimation pass over videos.

1. Choose the video list or video folder.
2. Set `destfolder` if you want all outputs in a dedicated analysis location.
3. Decide whether `save_as_csv` is needed in addition to the HDF output.
4. Use `batch_size` only when the model and hardware can actually support it.
5. Set `dynamic` for bottom-up dynamic cropping when it helps your data.
6. For multi-animal projects, decide whether `auto_track` should stay on.
7. Set `n_tracks` and `animal_names` consistently if the number of animals is known.
8. Use `use_shelve` when you need lower memory footprint and can live with shelf-backed output.
9. Set `overwrite=True` only when you want to replace prior analysis outputs.
10. Use `cropping` only when every analyzed video should share the same crop window.

Important notes:

- `auto_track=False` means the raw detections are only the first half of the workflow; hand off to multi-animal-tracking for tracklet conversion and stitching.
- `identity_only=True` is only meaningful when the model has learned identity.
- `inference_cfg` is the right place for inference-time runner choices.
- Top-down and CTD workflows need detector or condition handling to be valid.

## 6. Evaluation workflow

Use this to choose a good snapshot before running long inference jobs.

1. Evaluate one or more shuffles.
2. Compare bodyparts only if you want a focused metric.
3. Use `pcutoff` to match the confidence behavior you actually want.
4. Turn on plotting when you want to inspect the predicted vs. ground-truth overlay.
5. Add per-keypoint evaluation only when you need finer diagnostic detail.

Helpful patterns:

- compare all bodyparts first, then narrow to a subset
- use multiple shuffles when you want to compare split stability
- keep `pcutoff` aligned with the project bodyparts plus any unique bodyparts

## 7. Export workflow

Use export once you have a snapshot you trust.

1. Choose the shuffle and training fraction.
2. Pick the snapshot index or use the project default.
3. For top-down models, decide whether the detector should be exported too.
4. Use `wipepaths=True` when you want a bundle that is easier to relocate.
5. Leave `overwrite=False` unless you are replacing an export on purpose.

Outputs to expect:

- an `exported-models-pytorch` folder
- a `.pt` bundle for the selected pose snapshot
- a detector bundle inside the same export when the model uses a detector

## 8. Handoff after analysis

After `analyze_videos` or `analyze_images`, hand off to the next owner as needed:

- visual verification of predictions → labeled-video rendering in the post-processing sub-skill
- multi-animal tracklet conversion and stitching → the multi-animal-tracking sub-skill
- model export for reuse or live inference → stay here and use `export_model`

## 9. Quick preflight checklist

- The chosen shuffle has a PyTorch config.
- The requested snapshot exists.
- The device choice matches the hardware you actually have.
- Top-down runs have detector snapshots or an explicit detector-free export plan.
- `comparison_bodyparts`, `pcutoff`, `n_tracks`, and `animal_names` all agree with the project metadata.
