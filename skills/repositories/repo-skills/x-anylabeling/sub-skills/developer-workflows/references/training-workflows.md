# Ultralytics training workflows

This reference covers the X-AnyLabeling Ultralytics training surface and the hidden worker used by the GUI. It is for safe setup, inspection, and troubleshooting. It does not ask future agents to run repository examples or read source files.

## When to use this workflow

Use it when the user wants to train a YOLO-family model from labels already prepared in X-AnyLabeling, diagnose why the training tab will not start, inspect worker payload/event behavior, or export the best checkpoint from a completed training run.

The supported GUI task types are exactly:

- `Classify` for image-level flags.
- `Detect` for horizontal rectangles.
- `OBB` for rotated boxes.
- `Segment` for polygons.
- `Pose` for keypoints.

Dataset conversion or hand-authored YOLO/VOC/COCO conversion details are routed to `../conversion-cli/SKILL.md`.

## Installation and dependency posture

The base `x-anylabeling-cvhub` package can run annotation and conversion without Ultralytics. Training needs optional training packages, especially `ultralytics` and a compatible `torch` stack. Device availability depends on the local PyTorch build:

- `cuda` is available only when `torch.cuda.is_available()` is true.
- `mps` is available only when `torch.backends.mps.is_available()` is true.
- `cpu` is always the fallback device option when Torch is importable or absent from the GUI's device probe.

In this skill's construction environment, training dependencies, CUDA, TensorRT, model downloads, and actual training were not verified. Treat them as optional and local-environment-specific. Verify with the bundled safe validator before recommending a launch.

## GUI flow

1. Open the GUI and load a dataset of images with X-AnyLabeling labels.
2. Choose **Train → Ultralytics**.
3. In the **Data** tab:
   - Select one task type: `Classify`, `Detect`, `OBB`, `Segment`, or `Pose`.
   - Confirm the label summary has at least `20` valid labeled images for the chosen task. This threshold is enforced before training.
   - Confirm that labels use the expected shape family: flags for `Classify`, rectangles for `Detect`, rotations for `OBB`, polygons for `Segment`, and points for `Pose`.
4. In the **Configuration** tab, supply the basic settings:
   - `project`: output root directory.
   - `name`: run directory name inside the project.
   - `model`: pretrained `.pt` checkpoint path or bare `.pt` model name.
   - `data`: dataset YAML for detect/OBB/segment/pose, or a classification dataset directory when using a pre-organized classification dataset.
   - `device`: one of the device choices that the local Torch installation reports as available, usually `cpu`, `cuda`, or `mps`.
   - `dataset ratio`: train/validation split ratio for the generated dataset.
   - **Only Checked Files**: if enabled, the dataset builder includes only images whose X-AnyLabeling JSON has `checked: true`.
5. For `Pose`, provide a keypoint configuration YAML in addition to the data YAML. Missing keypoint configuration is a known validation failure.
6. Review the default hyperparameters or modify them under advanced settings.
7. Move to the **Train** tab and start only after the user accepts training side effects: dataset materialization, checkpoint downloads when using bare model names, GPU/CPU compute, logs, and output files.
8. After completion, use **Open Directory** for outputs and **Export** to export `weights/best.pt` to supported Ultralytics formats.

## Default training configuration

The training payload starts from these defaults unless the GUI/user overrides them:

| Key | Default |
|---|---:|
| `epochs` | `100` |
| `batch` | `16` |
| `imgsz` | `640` |
| `workers` | `8` |
| `classes` | empty string |
| `single_cls` | `false` |
| `time` | `0` |
| `patience` | `100` |
| `close_mosaic` | `10` |
| `optimizer` | `auto` |
| `cos_lr` | `false` |
| `amp` | `true` |
| `multi_scale` | `false` |
| `lr0` | `0.01` |
| `lrf` | `0.01` |
| `momentum` | `0.937` |
| `weight_decay` | `0.0005` |
| `warmup_epochs` | `3.0` |
| `warmup_momentum` | `0.8` |
| `warmup_bias_lr` | `0.1` |
| `hsv_h` | `0.015` |
| `hsv_s` | `0.7` |
| `hsv_v` | `0.4` |
| `degrees` | `0.0` |
| `translate` | `0.1` |
| `scale` | `0.5` |
| `shear` | `0.0` |
| `perspective` | `0.0` |
| `dropout` | `0.0` |
| `fraction` | `1.0` |
| `rect` | `false` |
| `box` | `7.5` |
| `cls` | `0.5` |
| `dfl` | `1.5` |
| `pose` | `12.0` |
| `kobj` | `2.0` |
| `save_period` | `-1` |
| `val` | `true` |
| `plots` | `false` |
| `save` | `true` |
| `resume` | `false` |
| `cache` | `false` |

Optimizer choices are `auto`, `SGD`, `Adam`, `AdamW`, `NAdam`, `RAdam`, and `RMSProp`.

## Dataset construction behavior

The GUI prepares a YOLO-style dataset under its work directory before calling Ultralytics:

- It counts valid images for the selected task type and rejects fewer than `20` valid labeled images.
- It shuffles valid labeled images before splitting by the dataset ratio.
- For non-classification tasks, it writes `images/train`, `images/val`, `labels/train`, and `labels/val` plus a generated `data.yaml`.
- For `Classify`, it creates `train/<class>` and `val/<class>` directories from image-level flags, then writes a generated classification `data.yaml`.
- When `skip_empty_files` is false, background images can be included in training for non-classification tasks.
- When **Only Checked Files** is true, missing labels and unchecked labels are skipped.
- For `Pose`, the label converter requires a pose keypoint YAML. If the config is absent, dataset creation returns a pose-config-required error instead of preparing labels.

For classification there are two modes:

1. **Flags-based classification**: use X-AnyLabeling image-level flags; the data field can be generated from annotations.
2. **Pre-organized classification dataset**: supply a dataset directory with `train/<class>/...` and optional `val/<class>/...` and `test/<class>/...` children.

## Basic validation semantics

The built-in basic validator requires:

- Non-empty `project`.
- Non-empty `name`.
- A run directory `<project>/<name>` that does not already exist, unless the GUI asks the user to confirm reuse/overwrite behavior.
- An existing model file path.
- An existing data path.

A bare model name such as `yolov8n.pt` is later handled by the worker payload path resolver, not by the basic existence check. For safe preflight outside the GUI, the bundled validator accepts both existing paths and bare `.pt` names, but reports that bare names may download via Ultralytics during the actual worker step.

## Hidden training worker facts

Training runs in a child process rather than directly on the GUI thread.

- The CLI subcommand is `train-worker`; it is hidden from ordinary help.
- The worker takes `--payload <json-file>`.
- The payload is a JSON object containing the training arguments. Before writing it, the manager resolves the `model` field.
- `build_training_worker_command(payload_path)` uses the current Python interpreter for source execution:

  ```text
  <python> -m anylabeling.app --work-dir <work-dir> train-worker --payload <payload.json>
  ```

- In a frozen executable, the command starts from the frozen executable and uses:

  ```text
  <frozen-executable> --work-dir <work-dir> train-worker --payload <payload.json>
  ```

- Worker event lines are prefixed exactly with:

  ```text
  __XANYLABELING_TRAIN_EVENT__=
  ```

  The suffix is JSON with an `event` field. Non-prefixed lines are treated as training logs.
- Terminal worker events are `training_completed` and `training_error`.
- `training_log` events carry a log `message`.
- The worker sets Matplotlib to the non-interactive `Agg` backend, constructs `ultralytics.YOLO(model)`, sets `verbose=False` and `show=False`, then calls `model.train(**train_args)`.
- On exceptions, the worker emits a `training_error` event with `error` and `traceback`, then exits nonzero.

## Model path resolution and downloads

The worker model resolver behaves as follows:

- Non-string model values are returned unchanged.
- HTTP(S) URLs are returned unchanged.
- Absolute paths are returned unchanged.
- Relative paths with a parent directory are returned unchanged.
- Names that do not end in `.pt` are returned unchanged.
- A bare `.pt` file name is cached in the training weights directory under the application work directory.
- If the cached bare-name checkpoint already exists, it is reused.
- Otherwise, the resolver calls Ultralytics' asset download helper. This may perform a network download during actual training startup.

## Stop and kill behavior

When the GUI asks to stop training:

- It sets a stop event.
- The child process is terminated.
- If it does not exit within about five seconds, the process tree is killed.
- On POSIX systems, the child is started in a process group and killed via the process group.
- On Windows, the process is started with a new process group when supported and force-killed with `taskkill /F /T /PID` as a fallback.
- A stopped job emits `training_stopped`; it is not the same as `training_completed`.

## Export after training

The GUI export action uses the completed run directory and expects:

```text
<project>/<name>/weights/best.pt
```

Supported export validators include ONNX, OpenVINO, TensorRT engine, CoreML, TensorFlow formats, Paddle, MNN, NCNN, IMX500, RKNN, and TorchScript. Missing exporter packages may be attempted with a short pip install timeout by the export manager. This can mutate the active environment; ask before allowing it in a controlled development environment.

ONNX export requires `onnx>=1.15.0`, `onnxslim>=0.1.59`, and `onnxruntime`. CPU ONNX Runtime was verified for the package baseline, but export success still depends on the trained checkpoint and local package versions.

## Safe preflight command

Use the bundled script from this sub-skill to validate common launch blockers without training:

```bash
python sub-skills/developer-workflows/scripts/check_training_config.py \
  --task-type Pose \
  --label-count 20 \
  --model yolov8n-pose.pt \
  --data pose-data.yaml \
  --project runs \
  --name pose-exp \
  --device cpu \
  --pose-cfg pose-keypoints.yaml
```

It checks task names, label threshold, required fields, pose keypoint config presence, local model/data/project/name shape, and Torch-reported device availability.
