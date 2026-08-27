# Tracking Troubleshooting

## Demo exits or shows no ROI window

Likely causes:

- The host is headless or OpenCV was installed without GUI support.
- The image sequence directory is empty or unreadable.
- The first frame cannot be loaded by OpenCV.

Recovery:

1. Validate `--base-path` with a simple directory listing and image load check.
2. Use a desktop/display session for interactive ROI selection.
3. Avoid `demo` mode on servers; use `test` mode without visualization for non-interactive checks.

## `--cpu` does not force the demo to CPU

The legacy demo accepts `--cpu` but selects `cuda` whenever PyTorch reports a visible CUDA device. If CPU-only demo behavior is required, hide GPUs from the process or use benchmark `test` mode, which honors `--cpu`.

## Checkpoint assertion fails

Symptoms: `Please download ... first` or `<path> is not a valid file`.

Recovery:

- Confirm whether the path is relative to the selected experiment directory or absolute.
- Use `--strict` with `scripts/run_tracking.py` to catch missing paths before execution.
- Match checkpoint family to config/flags: refine checkpoints with refine configs and `--mask --refine`, base mask checkpoints with `--mask`, SiamRPN checkpoints without mask flags.

## Dataset not found or no dataset choices available

The benchmark loader discovers datasets from checkout-local `data/` directories and JSON/index files. Run the data-preparation layout checker before testing:

```bash
python ../data-preparation/scripts/check_dataset_layout.py --data-root <siammask-checkout>/data --dataset vot --strict
```

For VOS data, check DAVIS/YouTube-VOS layouts instead of VOT.

## Result evaluation asserts no trackers

`eval` mode needs a result root containing tracker directories whose basename starts with `--tracker-prefix`. Confirm the wrapper's `test` or `tune` output path, then pass that directory as `--result-dir` and a matching prefix.

## Mask/refine output is empty or unstable

Likely causes:

- Wrong config/checkpoint pair.
- `--mask` or `--refine` flags not aligned with the trained model.
- Segmentation threshold `seg_thr` too high or tuned for another dataset.

Recovery:

1. Confirm the model family in the root model overview.
2. Use the dataset-specific config defaults before custom tuning.
3. Tune VOT or VOS parameters only after a baseline benchmark run succeeds.

## VOS tuning crashes on a CPU-only machine

`tune-vos` calls CUDA directly. Use a CUDA-capable environment or restrict the task to documentation/input validation. Do not present CPU-only checks as proof that VOS tuning is verified.

## Visualization crashes inside benchmark runs

Disable `--visualization` on headless machines. Use saved output files and evaluator metrics instead of `cv2.imshow` for automation.
