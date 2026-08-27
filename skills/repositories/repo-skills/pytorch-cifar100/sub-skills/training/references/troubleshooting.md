# Troubleshooting

## Purpose

Use this page when the training workflow, resume path, TensorBoard setup, or optional LR-finder constraints fail.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `the network name you have entered is not supported yet` | `-net` does not match a key in the network factory. | Run `scripts/build_train_command.py --list-nets`, pick one exact key, and rebuild the command. |
| `ImportError` around `SummaryWriter` or TensorBoard | TensorBoard support is missing from the environment. | Install TensorBoard in the target environment, then retry `train.py`. The import happens before training starts. |
| CIFAR-100 download errors, `URLError`, or permission problems under `./data` | Network is blocked, the cache is incomplete, or the working directory is not writable. | Restore network access, make the checkout writable, or pre-stage the CIFAR-100 data tree before rerunning. |
| `no recent folder were found` | `-resume` was requested but no non-empty `checkpoint/<net>/` folder exists. | Confirm that a prior run saved weights for the same `net`, or start a fresh run without `-resume`. |
| `no recent weights file were found`, `IndexError`, or malformed resume behavior | The latest checkpoint folder is empty or missing `.pth` files. | Clean partial checkpoint folders, keep at least one regular or best checkpoint in the latest run folder, then resume again. |
| `Torch not compiled with CUDA enabled` or `CUDA out of memory` | `-gpu` was used without a usable CUDA runtime, or the batch size is too large. | Omit `-gpu`, lower `-b`, or choose a smaller model before retrying. |
| `PermissionError` or log-folder failures under `runs/` or `checkpoint/` | The working tree is read-only or another process blocked folder creation. | Run from a writable checkout and remove stale partial output folders if needed. |

## What to check first

1. Validate the command with `scripts/build_train_command.py`.
2. Confirm the selected `-net` string is supported.
3. Confirm the checkout is writable and can create `./data`, `runs/`, and `checkpoint/`.
4. If resuming, inspect the latest `checkpoint/<net>/` folder and ensure it contains at least one `.pth` file.

## TensorBoard-specific notes

- `train.py` writes logs under `runs/<net>/<TIME_NOW>/`.
- If the log directory cannot be created, fix permissions before launching training.
- Graph creation happens early, so graph-tracing or device errors may appear before the first epoch.

## Resume-specific notes

- Resume always targets the most recent non-empty folder for the selected `net`.
- It does not let you choose an arbitrary historical checkpoint from the CLI.
- If you need a specific earlier run, adjust the checkpoint directory layout before resuming.

## Optional LR-finder notes

If the optional scan fails instead of the main trainer:

- Check that CUDA is available.
- Check that OpenCV is installed, because `cv2` is imported immediately.
- Make sure `num_iter` is large enough to survive the trimming step.
- Expect `result.jpg` to appear in the current working directory when the scan succeeds.
