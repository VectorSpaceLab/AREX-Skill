# Tracking/Evaluation Troubleshooting

## Missing or unset `local.py`

**Symptom**: runtime error says `YOU HAVE NOT SETUP YOUR local.py!!!` or dataset paths are empty.

**Likely cause**: PyTracking generated a default local file and stopped, or the file exists but still has empty paths.

**Recovery**:

1. In the target checkout, generate the default file if needed:
   ```bash
   python -c "from pytracking.evaluation.environment import create_default_local_file; create_default_local_file()"
   ```
2. Edit the generated local config and set at least `network_path`, `results_path`, and the selected dataset path.
3. Re-run a single short sequence before a full dataset.

## Unknown dataset alias

**Symptom**: `ValueError: Unknown dataset '...'`.

**Likely cause**: the alias does not match PyTracking's registry.

**Recovery**:

- Check [datasets and results](datasets-and-results.md) or run:
  ```bash
  python scripts/build_tracking_command.py --list-datasets
  ```
- Use `trackingnet` rather than `tn`, and `got10k_test`/`got10k_val` rather than ambiguous `got` names in this checkout.

## Tracker or parameter import failure

**Symptom**: import error for `pytracking.tracker.<name>` or `pytracking.parameter.<tracker>.<param>`.

**Likely causes**:

- Used a display label such as `DiMP-50` instead of `tracker=dimp`, `param=dimp50`.
- New tracker directory is missing `get_tracker_class()`.
- Parameter file is absent or has syntax/import errors.

**Recovery**:

- Use module names from [datasets and results](datasets-and-results.md) and the root catalog.
- For custom tracker layouts, route to the `tracker-development` sub-skill and run its static layout validator.

## Checkpoint or network path failure

**Symptom**: file-not-found while loading a `.pth`/`.pth.tar` model, or the tracker initializes but no model weights are available.

**Likely cause**: `network_path` is unset or does not contain the checkpoint expected by the selected parameter file.

**Recovery**:

1. Inspect the selected parameter file in the target checkout to identify the checkpoint filename.
2. Set `network_path` in local evaluation config.
3. Download/copy the checkpoint only with user approval because upstream model links are network downloads.
4. Re-run a single sequence/video with `debug=0`.

## CUDA, memory, or device failure

**Symptom**: CUDA unavailable, device mismatch, out-of-memory, or slow CPU fallback.

**Likely cause**: most published PyTracking trackers are PyTorch network-backed and upstream installation assumes an NVIDIA GPU.

**Recovery**:

- Verify `torch.cuda.is_available()` and a tiny CUDA allocation in the target environment.
- Start with a smaller tracker/parameter combination when possible, e.g. ATOM CPU-oriented `multiscale_no_iounet` can validate some mechanics but does not prove GPU model performance.
- Reduce parallel threads; dataset-level multiprocessing can amplify memory usage.
- Do not claim full tracker verification from CPU-only import checks.

## Visdom and GUI surprises

**Symptom**: Visdom connection warnings, Matplotlib/OpenCV window failures, or `--use_visdom False` still behaves as true.

**Likely causes**:

- `debug > 0` enables visualization paths.
- Native CLI uses `argparse type=bool`, so non-empty strings are truthy.
- Headless server lacks display/camera.

**Recovery**:

- Prefer `debug=0` for batch runs.
- Use Python API `visdom_info={'use_visdom': False}` for reliable control.
- If using the helper, `--visdom off` emits an empty-string workaround, but API control is safer.
- Do not run webcam/video GUI workflows in headless sessions without display forwarding.

## Full dataset run appears stuck

**Symptom**: long run with no obvious progress or missing output.

**Likely cause**: full benchmark evaluation can be slow, data-heavy, and GPU-bound.

**Recovery**:

1. Stop and re-run one known-short sequence with `threads=0`.
2. Confirm result path write permission.
3. Confirm dataset frames/annotations are readable.
4. Enable a low debug level only for an interactive diagnosis, not for unattended full evaluation.
