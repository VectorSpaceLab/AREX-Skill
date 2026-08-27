# Analysis and Packaging Troubleshooting

## Result file not found

Symptoms:

- `Result not found. .../<sequence>.txt`
- Packaging planner reports many missing box files.
- Analysis cache is generated over fewer sequences than expected.

Likely causes:

- Tracker results were never produced; route to `tracking-evaluation`.
- Dataset alias or sequence names differ from the result files.
- `run_id` was omitted or supplied incorrectly, so the expected directory is `parameter` instead of `parameter_000` or vice versa.
- The local PyTracking configuration points `results_path` somewhere else.

Fixes:

1. Confirm the tracker name, parameter name, and run ids used during tracking.
2. Inspect the result tree before analysis.
3. For official package planning, run the bundled planner with `--results-root`.
4. Use `skip_missing_seq=True` only for exploratory plots; do not use it to declare an official package complete.

## Invalid bounding boxes or metric errors

Symptoms:

- `Error: Invalid results`
- `Nans in calculated overlap`
- Misleading plots after a tracker failure.

Likely causes:

- Box files contain NaNs.
- Width or height is negative.
- Rows do not have four values.
- A failed tracker wrote status strings or mixed delimiters into result files.

Fixes:

1. Validate each box file as numeric `N x 4` before plotting.
2. Repair or rerun the tracker for corrupted sequences.
3. Treat zero-size predictions carefully: PyTracking may carry previous predictions forward, but negative sizes and NaNs are fatal.
4. Do not average failed runs into a final report.

## Prediction/ground-truth length mismatch

Symptoms:

- `Mis-match in tracker prediction and GT lengths`
- Sequence scores look padded or truncated.

Likely causes:

- Tracking stopped early.
- Result file includes an extra initialization row or skipped a frame.
- Dataset version differs from the result files.

Fixes:

1. Check the expected frame count from the dataset object.
2. Check whether the tracker wrote one row per frame including frame 0.
3. Rerun affected sequences if official reporting matters.
4. Avoid manual trimming unless the benchmark protocol explicitly permits it.

## Cached `eval_data.pkl` does not match current trackers or dataset

Symptoms:

- New plots show old tracker labels.
- A changed dataset/tracker list silently uses stale metrics.

PyTracking validates cached sequence names and `(name, parameter, run_id)` tuples. If labels changed but identity did not, display names may update without recomputing. If in doubt, pass `force_evaluation=True` to plotting or remove the report cache directory.

## Plotting fails in a headless session

Symptoms:

- Matplotlib display errors.
- `plt.show()` blocks forever.
- PDF files are not created in batch jobs.

Fixes:

1. Set a non-interactive backend before importing plotting modules, for example `MPLBACKEND=Agg` or `matplotlib.use('Agg')`.
2. Ensure the configured plot directory is writable.
3. Avoid `playback_results(...)` on headless machines; it is GUI-oriented.
4. If optional TeX/TikZ support is missing, prefer PDF plot outputs and avoid custom TikZ export code.

## VOS evaluation mask errors

Symptoms:

- Missing mask files under a sequence directory.
- Indexed-mask image loader errors.
- J scores are unexpectedly zero.

Likely causes:

- Mask names do not match annotation frame names.
- Masks are RGB visualization images rather than indexed labels.
- Object ids do not match initialization metadata.
- VOS dataset paths are not configured.
- Modern NumPy removed legacy aliases used by older VOS utilities (`np.bool`, `np.int`).

Fixes:

1. Confirm the result tree is `<segmentation_dir>/<sequence>/<frame-name>.png`.
2. Verify masks are indexed labels with background id 0 and target object ids as integers.
3. Test one sequence before evaluating the full dataset.
4. If legacy NumPy alias failures occur, use a compatible environment or patch the local runtime before claiming VOS support.

## GOT-10k package is incomplete

Symptoms:

- Missing files for `GOT-10k_Test_000001` through `GOT-10k_Test_000180`.
- Missing `parameter_001` or `parameter_002` run directories.
- Missing `_time.txt` files.

Fixes:

1. Run the planner for GOT-10k with the result root.
2. Confirm exactly three runs are available: `000`, `001`, and `002`.
3. Confirm each sequence has both `<seq>.txt` and `<seq>_time.txt` in every run directory.
4. Do not upload a zip created from a partial tree.

## TrackingNet package completeness cannot be proven

Symptoms:

- The planner reports inspected files but warns that no official sequence list was provided.
- Native packer fails while building `get_dataset('trackingnet')`.

Fixes:

1. Supply `--trackingnet-sequence-list` to the planner if available.
2. In a configured PyTracking environment, ensure the TrackingNet dataset path is set so the native registry can enumerate test sequences.
3. Confirm whether the run directory is `parameter` or `parameter_000` before packaging.

## Raw result download or unpack problems

Symptoms:

- Google Drive quota or network errors.
- Archives unpacked into an unexpected result root.
- Existing result directories overwritten or mixed with downloaded results.

Fixes:

1. Ask for explicit download/unpack approval and target paths.
2. Download to a temporary cache first.
3. Unpack into a new empty directory when possible.
4. Keep archives until the user verifies results.
5. Retry network errors only when the user still wants the download and disk space is sufficient.

## VOT TraX support not found

Symptoms:

- `TraX support not found. Please add trax module to Python path.`
- VOT toolkit starts but cannot import the tracker.
- Native TraX library/link errors.

Fixes:

1. Confirm the same Python interpreter imports both PyTracking and `trax`.
2. Add TraX Python support paths only for the VOT invocation, not globally unless the user wants that.
3. Ensure native TraX library paths are visible to the process launched by the VOT toolkit or MATLAB wrapper.
4. Replace placeholder VOT paths with real environment-specific values.
5. Choose the correct region format and channel mode for the challenge.

## Archive overwrite risk

Symptoms:

- Existing `<output-name>.zip` is present.
- Staging directory from a previous package remains.

Fixes:

1. Use a unique output name that includes tracker, parameter, run id if applicable, and date or experiment id.
2. Do not overwrite an existing official upload archive unless the user explicitly approves.
3. Remember that the upstream packers remove their staging directories after archiving; preserve raw result trees separately.
