# VOT and Result Packaging

This reference covers safe planning for official result packages and VOT integration. It does not replace benchmark rules from the official evaluation servers; use it to avoid local layout mistakes before creating archives.

## Use the bundled planner first

The bundled planner checks expected input paths and prints the archive/staging plan without creating zips:

```bash
# From this sub-skill directory, or with the bundled script path resolved explicitly:
python scripts/plan_result_packaging.py --help
```

Examples:

```bash
# GOT-10k: expect 180 test sequences and run ids 000, 001, 002.
python scripts/plan_result_packaging.py \
  got10k --tracker-name dimp --parameter-name dimp50 --results-root /path/to/results

# TrackingNet: validate against an explicit sequence list when available.
python scripts/plan_result_packaging.py \
  trackingnet --tracker-name dimp --parameter-name dimp50 --run-id 0 \
  --results-root /path/to/results --trackingnet-sequence-list trackingnet_test_sequences.txt
```

The planner avoids PyTracking imports so it can diagnose a result tree even when the package environment is not currently importable. It never downloads data, runs trackers, trains models, or writes archives by default.

## GOT-10k packaging protocol

PyTracking's GOT-10k packer expects a result tree with three runs for each of the 180 test sequences.

Input shape under `results_root`:

```text
<tracker-name>/
  <parameter-name>_000/
    GOT-10k_Test_000001.txt
    GOT-10k_Test_000001_time.txt
    ...
  <parameter-name>_001/
    GOT-10k_Test_000001.txt
    GOT-10k_Test_000001_time.txt
    ...
  <parameter-name>_002/
    GOT-10k_Test_000001.txt
    GOT-10k_Test_000001_time.txt
    ...
```

Each box file is loaded as floating-point values and written with comma delimiters. Each time file must exist for every run and sequence. The upstream staging layout is:

```text
<output-name>/
  GOT-10k_Test_000001/
    GOT-10k_Test_000001_1.txt
    GOT-10k_Test_000001_2.txt
    GOT-10k_Test_000001_3.txt
    GOT-10k_Test_000001_time.txt
  ...
```

The final archive is `<output-name>.zip` under the configured GOT packed-results directory. The upstream packer removes the staging directory after creating the zip. Plan this carefully because it is destructive to the staging directory, not to the raw result tree.

Notes:

- Run ids are zero-based in PyTracking result directories (`000`, `001`, `002`) and one-based in staged GOT-10k filenames (`_1`, `_2`, `_3`).
- A missing run or time file should block packaging.
- Protocol completeness is 180 sequences named `GOT-10k_Test_000001` through `GOT-10k_Test_000180`.

## TrackingNet packaging protocol

PyTracking's TrackingNet packer uses the dataset registry to enumerate sequences and writes one text file per sequence into the staging directory.

Input shape without a run id:

```text
<tracker-name>/
  <parameter-name>/
    <sequence-name>.txt
```

Input shape with a run id:

```text
<tracker-name>/
  <parameter-name>_000/
    <sequence-name>.txt
```

Staging/output shape:

```text
<output-name>/
  <sequence-name>.txt
<output-name>.zip
```

The upstream packer writes comma-delimited values with two decimal places. If `output_name` is omitted, PyTracking derives it as `<tracker>_<parameter>` or `<tracker>_<parameter>_<run_id:03d>`.

Completeness requires the official TrackingNet test sequence list. When a PyTracking environment and dataset config are available, the original packer obtains that list from `get_dataset('trackingnet')`. For environment-independent planning, pass `--trackingnet-sequence-list` to the bundled planner. If no list is provided, the planner can inspect the existing result directory but cannot prove official completeness.

## Raw result download and unpack safety

PyTracking includes utilities for Google Drive raw-result downloads and archive unpacking. Treat these as network and filesystem mutation steps, not analysis steps.

Before downloading or unpacking:

1. Ask for explicit approval if the user did not already authorize downloads.
2. Identify the download cache directory and final result root.
3. Check available disk space; raw multi-tracker result archives can be large.
4. Avoid unpacking directly over valuable existing results. Prefer a new empty result root or a reviewed merge plan.
5. Preserve downloaded archives until the user confirms the unpacked result tree is complete.
6. Record which tracker groups were requested: PyTracking trackers, external trackers, all trackers, or selected tracker/parameter pairs.

Raw model-zoo benchmark boxes use `[top_left_x, top_left_y, width, height]`. Raw VOS segmentation results are separate archive material and should be validated as indexed masks before `evaluate_vos(...)`.

## Distractor dataset generation boundary

The repo's distractor dataset helper runs trackers through a dataset and writes candidate-state JSON. That is not a passive analysis/packaging helper. If the user asks to generate or debug distractor datasets, route to `tracking-evaluation` for tracker execution planning and to `tracker-development` if tracker internals or candidate maps must be modified.

## VOT integration planning

PyTracking has both Python and MATLAB-style VOT integration examples. Plan the following pieces before running VOT:

1. **VOT toolkit**: installed and configured separately from PyTracking.
2. **TraX support**: Python `trax` module importable for `traxpython` integration, with native libraries discoverable when required.
3. **Tracker command**: imports the PyTracking VOT runner and calls a tracker/parameter pair such as a DiMP parameter.
4. **Path configuration**: the VOT tracker configuration must point to the PyTracking package/check-out and TraX Python support path without hard-coded stale local paths.
5. **Region and channel mode**: Python VOT wrapper supports rectangle and polygon region formats and channel modes such as color, RGB-D, RGB-T, or infrared.
6. **Debug behavior**: debug/Visdom settings should be intentionally set; VOT automation usually needs non-interactive behavior.

A minimal VOT tracker entry uses the `traxpython` protocol, a Python command that imports the VOT runner, and a path field for the PyTracking package. MATLAB-style wrappers additionally specify the Python interpreter, PyTracking path, TraX path, and native link paths. These are environment-specific values and must be supplied by the user or discovered in the active runtime environment; do not copy placeholder paths into a production configuration.

Common VOT planning questions:

- Which tracker and parameter file should be evaluated?
- Does the parameter file correspond to a VOT-specific configuration or a regular benchmark configuration?
- Is the selected VOT challenge expecting rectangle or polygon regions?
- Are TraX Python bindings importable from the same Python interpreter that imports PyTracking?
- Will the VOT toolkit invoke a shell command, MATLAB wrapper, or Python wrapper?

## When to create actual archives

Only create official zips after all are true:

- The user explicitly requested packaging, not just planning.
- The result root and packed-output root are identified.
- The dry-run plan has no blocking missing files.
- The target archive name will not accidentally overwrite an important previous upload, or overwrite is explicitly accepted.
- For TrackingNet, completeness was checked against a trusted sequence list or by running the native packer in a configured PyTracking environment.
