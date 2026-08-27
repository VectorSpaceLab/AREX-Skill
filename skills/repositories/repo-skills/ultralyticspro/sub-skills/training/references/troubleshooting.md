# Training Troubleshooting

## Purpose

Read this when a training preset fails or the source script cannot be mapped
cleanly.

## 1. Packaged config missing

**Symptom**

- `train_v8`, `train_yolo11`, or similar presets fail before training starts.

**Likely cause**

- The preset points at a config file that is not present in the active
  `ultralytics` install.

**Recovery**

- Use the bundled preset names rather than hard-coded repo-local paths.
- Confirm the file exists with `scripts/check_ultralytics_env.py --json`.
- For `train-yolo12`, supply a custom local `yolo12.yaml` or choose a different
  preset.

## 2. Dataset YAML not available

**Symptom**

- The run fails when `coco128.yaml`, `mnist160`, `dota8.yaml`, `coco8-pose.yaml`,
  or `coco8-seg.yaml` is resolved.

**Likely cause**

- The dataset has not been downloaded or cached locally yet.

**Recovery**

- Allow the first Ultralytics download if the environment has network access.
- Or stage the dataset before running `--execute`.
- If you only need to inspect the command, stay in dry-run mode.

## 3. Device mismatch

**Symptom**

- A preset fails because it requests `device=0` on a machine without a visible
  CUDA device.

**Likely cause**

- The source example assumed a GPU.

**Recovery**

- Override with `--device cpu`.
- Or install a CUDA-enabled PyTorch build and verify CUDA availability before
  launching the run.

## 4. Excessive runtime for CPU runs

**Symptom**

- The job starts successfully but is too slow to be practical.

**Likely cause**

- The source example was designed as a short demo, not a production-scale CPU
  training configuration.

**Recovery**

- Reduce `--epochs`, `--imgsz`, `--batch`, or `--workers`.
- Keep the helper in dry-run mode if the user only needs a plan.

## 5. `train-yolo12` cannot start

**Symptom**

- The helper prints that the preset needs a local `yolo12.yaml` file.

**Likely cause**

- The verified public Ultralytics install did not ship `cfg_yolov12/yolo12.yaml`.

**Recovery**

- Provide the local config file explicitly with `--model /path/to/yolo12.yaml`.
- Or switch to a packaged preset such as `train-yolo11`.

## 6. First-run weight or checkpoint download

**Symptom**

- The job pauses to fetch a model weight or checkpoint.

**Likely cause**

- The pretrained asset is not cached in the current environment.

**Recovery**

- Let the download complete, or pre-stage the weight file.
- Keep dry-run mode if the user does not want network activity.
