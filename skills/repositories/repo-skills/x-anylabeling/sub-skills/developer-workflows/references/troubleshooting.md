# Developer workflow troubleshooting

Use this reference to diagnose training, worker, packaging, localization, exporter, and contribution-preflight failures without immediately launching expensive or side-effectful commands.

## Ultralytics or Torch missing

Symptoms:

- Training tab cannot start a job.
- Worker exits with `Failed to import ultralytics` or `No module named ultralytics`.
- Device list has only CPU or the safe validator reports that Torch is not installed.

Actions:

1. Confirm whether the user actually intends to train. Training dependencies are optional.
2. Install a compatible `ultralytics` and `torch` stack only in an environment meant for training.
3. For GPU training, install a PyTorch build that matches the local CUDA stack; do not rely on the X-AnyLabeling GPU extra alone as proof that PyTorch CUDA is available.
4. Re-run the safe validator with `--device cpu`, `--device cuda`, or `--device mps` as appropriate.

## Too few labeled images

Symptoms:

- Validation says fewer than `20` labeled images were found.
- The Data tab blocks progression.

Actions:

- Confirm the selected task type matches the label shape family.
- Count only valid labeled images for the selected task: flags for `Classify`, rectangles for `Detect`, rotations for `OBB`, polygons for `Segment`, and points for `Pose`.
- If **Only Checked Files** is enabled, unchecked images do not count.
- Add labels or switch to a task type matching existing labels.

## Pose keypoint YAML missing

Symptoms:

- Pose dataset creation fails with a pose configuration required error.
- The safe validator rejects `--task-type Pose` without `--pose-cfg`.

Actions:

- Provide a keypoint YAML describing pose keypoints/skeleton in the expected format for the label converter and Ultralytics training.
- Ensure the YAML path exists before launching training.
- Ensure point labels in the dataset correspond to the expected keypoints.

## Dataset directory or YAML mismatch

Symptoms:

- Basic validation says the data path is invalid.
- Ultralytics reports missing images, labels, `names`, `train`, or `val` fields.
- Classification training finds no classes.

Actions:

- For `Detect`, `OBB`, `Segment`, and `Pose`, supply a dataset YAML with class `names` and valid train/val paths.
- For pre-organized `Classify`, supply a directory with `train/<class>/...`; optional `val/<class>/...` and `test/<class>/...` can be present.
- For GUI-generated datasets, inspect the generated `dataset_info.txt` and `data.yaml` in the run's dataset output if available.
- Route format conversion and schema repair to `../conversion-cli/SKILL.md` or `../annotation-ui/SKILL.md` depending on whether the issue is conversion or annotation content.

## Device unavailable

Symptoms:

- The safe validator reports CUDA/MPS unavailable.
- `cuda` is requested but `torch.cuda.is_available()` is false.
- `mps` is requested but `torch.backends.mps.is_available()` is false.

Actions:

- Use `cpu` for a functional but slower run.
- Install a Torch build that matches the requested hardware backend.
- Verify driver/runtime compatibility outside X-AnyLabeling.
- Treat CUDA, MPS, and TensorRT as optional unless the user explicitly requires them and provides compatible hardware.

## Model path or bare `.pt` surprises

Symptoms:

- A bare model name such as `yolov8n.pt` triggers network activity.
- Basic GUI validation rejects a model path that the worker would otherwise download.

Actions:

- Existing absolute/relative file paths are used as-is.
- Bare `.pt` names are cached under the training weights directory and may download through Ultralytics if absent.
- If network access is not allowed, require an existing local checkpoint path.
- Use the bundled validator to flag bare-name download risk before launch.

## Payload and event parsing

Symptoms:

- Training logs appear but progress/status does not update.
- Worker output contains malformed event lines.
- A wrapper cannot distinguish logs from terminal events.

Facts and actions:

- Event lines must start with `__XANYLABELING_TRAIN_EVENT__=` and then valid JSON.
- JSON must contain an `event` key.
- Terminal events are `training_completed` and `training_error`.
- Non-prefixed lines are ordinary training logs.
- Malformed prefixed lines should be displayed as logs rather than crashing the UI.
- A synthetic event parser test can be performed without launching training by feeding example strings into an equivalent parser.

## Training stop or kill behavior

Symptoms:

- Stop button appears not to terminate immediately.
- Child process remains after termination.

Facts and actions:

- Stop requests set a stop event, then terminate the child process.
- If it does not exit within about five seconds, the process tree is killed.
- POSIX uses process groups; Windows uses a new process group where possible and can fall back to `taskkill /F /T /PID`.
- Treat `training_stopped` as user cancellation, not as success or model export readiness.

## Export after training fails

Symptoms:

- Export button reports missing weights.
- Export manager attempts to install packages and fails.
- Output file is not found after export.

Actions:

- Confirm `<project>/<name>/weights/best.pt` exists.
- Confirm the export format and required packages. ONNX export needs `onnx>=1.15.0`, `onnxslim>=0.1.59`, and `onnxruntime`.
- Ask before allowing automatic package installation in a controlled environment.
- If exported files are created under a different extension/path, inspect the weights directory for format-specific output.

## PyInstaller missing or target mismatch

Symptoms:

- `Required command 'pyinstaller' was not found.`
- `System value '...' is not recognized.`
- `Required file '...spec' was not found.`

Actions:

- Install developer build dependencies that include PyInstaller.
- Use exactly one of `win-cpu`, `win-gpu`, `linux-cpu`, `linux-gpu`, or `macos`.
- Confirm the selected target's spec file exists.
- Confirm the environment extra matches the CPU/GPU target.
- Do not run the build just to diagnose target parsing; inspect command availability and spec existence first.

## GPU packaged app cannot load providers

Symptoms:

- A GPU build runs but only CPU provider is available.
- Windows app fails to load ONNX Runtime provider DLLs.
- Linux GPU executable cannot locate provider shared libraries.

Actions:

- Confirm the active build environment installed a GPU extra, not `cpu`.
- Verify CUDA/cuDNN compatibility for the ONNX Runtime GPU version.
- On Windows, inspect whether ONNX Runtime DLLs were bundled into `onnxruntime/capi` and whether the runtime hook can add that directory.
- On Linux, inspect whether CUDA provider `.so` files were present at build time and bundled by the GPU spec.

## `lrelease`, `pyrcc`, or `rcc` missing

Symptoms:

- Translation compile raises `No Qt translation compiler found`.
- Resource compile prints that no Qt resource compiler was found.

Actions:

- Install Qt Linguist tools or ensure `pyside6-lrelease` is in the active environment.
- Install PyQt6/PySide6 developer tools that provide `pyrcc6`, `pyside6-rcc`, or `rcc`.
- Re-run compile only in a source-controlled development checkout because it mutates generated files.

## Generated resource side effects

Symptoms:

- Large diff in generated `resources.py`.
- Import errors mention `PySide6` in a PyQt6 runtime.
- Runtime cannot read resource compression.

Actions:

- Do not hand-edit generated resources.
- Ensure generated imports are normalized to `PyQt6`.
- Prefer zlib compression when the resource compiler supports it.
- Review source `.qrc`, translations, icons, and UI files to find the real change.

## Exporter utility failures

Symptoms:

- Missing external modules such as `groundingdino`, `ram`, model-specific `models`, or `utils`.
- Missing checkpoint/ONNX/image files.
- CUDA provider unavailable.

Actions:

- Treat the ONNX exporter utilities summarized in `model-exporters.md` as reference-only unless all external prerequisites are provided.
- Ask for the external model repo/package, checkpoint path, output directory, device, and tiny test image.
- Do not download weights, fetch external code, or patch upstream model code without explicit approval.

## AGPL notice for Ultralytics

Ultralytics is AGPL-3.0. If the training feature is used or exposed as a network service, source-disclosure obligations may apply. Preserve the notice in user-facing training documentation and ask for legal/release review for productized network services.
