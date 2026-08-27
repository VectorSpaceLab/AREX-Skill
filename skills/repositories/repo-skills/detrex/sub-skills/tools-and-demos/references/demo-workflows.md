# Demo and Workflow Notes

This file explains how to choose between the supported tool workflows and what the safe command builder should preserve when it prints a plan.

## Choose the smallest matching route

- **Single image or image glob** → generic demo
- **Video file** → generic demo
- **Webcam stream** → generic demo, interactive only
- **Dataset annotations** → `visualize_data` with `annotation`
- **Augmented training samples** → `visualize_data` with `dataloader`
- **Saved prediction JSON** → `visualize_json_results`
- **FLOPs, activations, parameters, or structure** → `analyze_model`
- **Training / inference / data speed** → `benchmark`
- **Tracking sequence** → project-specific MOT route, reference-only here

## Generic demo workflow

### Before building the command

Confirm:

- the config file that matches the model family
- the checkpoint or init override that the config should load
- the input mode: image, video, or webcam
- the output target: file, directory, or interactive window
- whether a confidence threshold or metadata dataset override is needed

### Builder behavior

- Use `--input` for images and image globs.
- Use `--video-input` for a single video file.
- Use `--webcam` only for a live stream.
- Add `--opts train.init_checkpoint=...` when the user supplies a checkpoint.
- Keep other overrides at the end of the command.

### Output handling

- One image can save to a single file.
- Multiple images should save to an existing directory-style output target.
- Video output may be an `.mp4` or `.mkv` depending on OpenCV codec support.
- If no output is provided, the script opens a window instead of saving results.

## Analysis workflow

### Use this when you need

- parameter counts
- model structure summaries
- FLOPs estimates
- activation counts

### Builder behavior

- `parameter` and `structure` can be planned without a checkpoint.
- `flop` and `activation` should carry a checkpoint override and a bounded `--num-inputs` value.
- Keep the launcher to one GPU.
- Treat `num_inputs` as a runtime cap, not a dataset scan.

## Visualization workflow

### Raw annotations

Use `visualize_data --source annotation` when you want to inspect dataset labels directly. The helper should point at the config that defines the dataset and should steer the output into a directory.

### Dataloader samples

Use `visualize_data --source dataloader` when you want to inspect the post-augmentation pipeline. The helper should warn that the dataloader can be effectively unbounded.

### Saved predictions

Use `visualize_json_results` when you already have COCO/LVIS-style prediction JSON. The helper should require a dataset name and save a directory of side-by-side visualizations.

## Benchmark workflow

Use the benchmark route when you only need the command plan for timing or throughput. The helper should not execute the command, should not infer a dataset, and should not invent a multi-node layout.

### Builder behavior

- Preserve the requested `--task`.
- Carry through launch arguments such as `--num-gpus` and `--num-machines`.
- Refuse or warn on `eval` configurations that are not single-GPU and single-node.
- Keep benchmark commands explicit because the underlying runs can be expensive.

## MOT / tracking caveat

The generic helper does not wrap the project-specific MOT demo path. Use it only when the user explicitly needs sequence tracking and has a tracking-capable checkpoint and contiguous frames from one scene.

### Why it is special

- tracking state persists across frames
- unrelated still images can produce misleading trajectories
- some project READMEs route tracking through project launchers instead of the generic demo entry point

### Safe routing rule

If the user only needs object detection, choose the generic demo route instead of the tracking route.

## Command-plan etiquette

- Do not add automatic downloads.
- Do not assume the checkpoint is available unless the user supplied it or the config already declares one.
- Do not silently replace a file target with a directory target, and do not assume a new directory path already exists.
- Use JSON output when another agent needs to inspect the plan programmatically.
- If the user asks only for planning, stop after printing the command plan.
