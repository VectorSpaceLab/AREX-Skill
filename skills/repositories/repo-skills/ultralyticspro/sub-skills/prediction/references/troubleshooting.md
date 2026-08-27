# Prediction Troubleshooting

## Purpose

Read this when a prediction preset fails or the source image does not work as
expected.

## 1. Weight download on first execution

**Symptom**

- The run pauses to fetch `yolov8n.pt`, `yolo11n.pt`, or `yolov10n.pt`.

**Likely cause**

- The pretrained weights are not cached in the active environment.

**Recovery**

- Let the download finish if network access is allowed.
- Pre-stage the weight file before running `--execute`.
- Stay in dry-run mode if the user only wants the command plan.

## 2. Source image not found

**Symptom**

- The run errors out on a custom `--source` path.

**Likely cause**

- The source file does not exist or is not readable from the current machine.

**Recovery**

- Use the packaged default `assets/zidane.jpg` or supply a valid path.
- If the input is remote, make sure the runtime is allowed to access it.

## 3. Output directory issues

**Symptom**

- Saving fails because the project directory or run name cannot be created.

**Likely cause**

- The target directory is unwritable or the run name contains invalid path
  characters.

**Recovery**

- Override `--project` and `--name` with safe writable values.
- Keep `--save` off if the user only needs a dry run.

## 4. Device mismatch

**Symptom**

- Prediction fails when a GPU device is requested on a CPU-only environment.

**Likely cause**

- The preset or override forced a CUDA device that is not available.

**Recovery**

- Override with `--device cpu`.
- Or install a CUDA-enabled torch build and re-check CUDA availability.

## 5. Too many files or no visible output

**Symptom**

- The wrapper runs but the user cannot find the saved prediction image.

**Likely cause**

- A different `project` directory or run `name` was used than expected.

**Recovery**

- Re-run the dry-run to confirm the effective kwargs.
- Then set explicit `--project` and `--name` values before `--execute`.
