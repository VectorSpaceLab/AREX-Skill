# Troubleshooting

## Purpose

Read this when a lane-detection workflow fails and you need a quick symptom-to-fix map.

## Missing dependencies or imports

### Symptoms
- `ModuleNotFoundError: No module named 'addict'`
- `ModuleNotFoundError: No module named 'pathspec'`
- `ImportError` from `torch`, `torchvision`, `cv2`, `scipy`, or `sklearn`

### Likely causes
- The environment only has a partial runtime stack.
- The repo requirements were not installed.
- A system-site package conflicts with the private environment.

### Recovery
- Run the root smoke helper first: `python scripts/check_environment.py --repo-root . --device cpu`.
- Install the missing runtime packages that the repo scripts import.
- Re-run the smoke helper with `--device cuda` when GPU support is expected.

## CUDA or `.cuda()` failures

### Symptoms
- `AssertionError` or `RuntimeError` when scripts call `.cuda()`
- `CUDA not available` or `no kernel image is available`
- `Could not find cuda drivers on your machine`

### Likely causes
- CPU-only PyTorch build.
- CUDA wheel/driver mismatch.
- Unsupported GPU architecture.

### Recovery
- Use the training, evaluation, demo, or speed sub-skill only on a CUDA-capable environment.
- Verify a tiny CUDA tensor allocation before running the native scripts.
- If CUDA is not available, treat the GPU-native workflows as unverified rather than falling back silently.

## Dataset path and layout mistakes

### Symptoms
- `FileNotFoundError` for `train_gt.txt`, `test.txt`, or split lists.
- TuSimple conversion produces no masks or no list files.
- CULane evaluation finds no split inputs or no `list/test_split/*.txt` files.

### Likely causes
- `data_root` points at the wrong dataset root.
- The TuSimple JSON files are missing or not in the documented root layout.
- CULane images/lists were unpacked into the wrong directory level.

### Recovery
- Read `sub-skills/data-and-config/` and verify the dataset layout before rerunning training or evaluation.
- Re-run the bundled conversion helper for TuSimple when masks and list files are missing.

## Checkpoint and model mismatches

### Symptoms
- Evaluation or export cannot load a checkpoint.
- State dict keys have `module.` prefixes.
- Output shapes do not match the expected CULane/TuSimple dimensions.

### Likely causes
- The checkpoint came from DDP and was saved with `module.` prefixes.
- `griding_num`, `num_lanes`, `backbone`, or `use_aux` do not match the checkpoint.
- The user selected the wrong dataset family.

### Recovery
- Check the training sub-skill for the checkpoint conventions.
- Confirm the data/config sub-skill for the correct `cls_dim` and row anchors.
- In evaluation, use the helper that strips compatible prefixes when loading a checkpoint.

## CULane evaluator build failures

### Symptoms
- `cmake` or `make` errors in `evaluation/culane/`
- Missing OpenCV C++ headers or libraries
- Evaluator binary not found during CULane scoring

### Likely causes
- The host does not have OpenCV development files or a usable C++ toolchain.
- The evaluator was never built.

### Recovery
- Build the evaluator with the commands documented in `sub-skills/evaluation-and-visualization/`.
- If the host cannot compile the evaluator, record the limitation and keep the rest of the evaluation guidance usable.

## Speed and export caveats

### Symptoms
- `export.py` fails because the checkpoint path is hardcoded.
- `speed_real.py` hangs on camera/video input.
- TorchScript or LibTorch examples fail with wrong device or half precision assumptions.

### Likely causes
- The source scripts were written as repo-local demos, not portable CLI tools.
- The user is trying to run a camera benchmark without a camera/video source.
- The exported model or benchmark dimensions do not match the lane model configuration.

### Recovery
- Use the bundled export and benchmark helpers in `sub-skills/export-and-speed/` instead of the raw source script.
- Prefer `speed_simple.py`-style synthetic checks before camera-based measurement.

## When to stop

Stop and escalate when:
- Required CUDA hardware is missing.
- A dataset or checkpoint is not available.
- The CULane evaluator cannot be built because system packages are missing.
- A benchmark would require a real camera, video source, or large dataset download.
