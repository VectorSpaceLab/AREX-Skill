# Norfair evaluation troubleshooting

## `norfair`, `motmetrics`, or `pandas` is missing

**Symptom:** `norfair.metrics` raises an import error, the bundled helper says metrics dependencies are unavailable, `Norfair is not importable`, or `Accumulators.create_accumulator()` fails immediately.

**Cause:** The evaluation path needs Norfair plus `motmetrics` and `pandas`. The source `norfair.metrics` module imports `motmetrics` and `pandas` lazily and falls back to a dummy placeholder when they are missing.

**Fix:** Install the metrics extras in the environment that will run evaluation:

```bash
pip install norfair[metrics]
```

If you already manage dependencies manually, make sure `norfair`, `motmetrics`, and `pandas` are installed together. If the helper later complains about the LAP solver, add `scipy` too.

**Do not confuse:** a successful `python scripts/motchallenge_eval.py --help` run does not mean metrics dependencies are present; it only proves the CLI can parse options.

## The dataset folder is missing or the split is wrong

**Symptom:** The helper cannot find `seqinfo.ini`, `gt/gt.txt`, or `det/det.txt`; or it fails because the dataset has no labels.

**Cause:** The evaluator expects MOTChallenge sequence folders under a labeled split, usually `train/`. The `test/` split does not provide labels.

**Fix:** Point the helper at the labeled split and verify each sequence folder contains the expected files:

```text
<dataset-root>/<sequence>/seqinfo.ini
<dataset-root>/<sequence>/gt/gt.txt
<dataset-root>/<sequence>/det/det.txt
```

If you only have one sequence folder, pass that sequence folder directly.

## `seqinfo.ini` is malformed

**Symptom:** `InformationFile.search()` raises `ValueError`, `seqLength` comes back as a string, or frame iteration breaks with a type error.

**Cause:** `InformationFile.search()` is intentionally simple. It expects lines that start with the exact key name and a plain `key=value` layout.

**Fix:** Make sure `seqinfo.ini` contains clean integer fields, especially `seqLength`. Avoid spacing like `seqLength = 100`; use `seqLength=100` instead.

If you are also using frame/video helpers elsewhere, `frameRate`, `imWidth`, `imHeight`, `imDir`, and `imExt` must follow the same plain formatting.

## `gt/gt.txt` or `det/det.txt` has the wrong shape

**Symptom:** `numpy.loadtxt` fails, the parser returns nonsense, or `mm.io.loadtxt` refuses the ground-truth file.

**Cause:** MOTChallenge files are comma-separated and must keep the expected column layout.

**Fix:** Verify the file shape before scoring:

- `det/det.txt` must follow the 10-column detection layout used by `DetectionFileParser`.
- `gt/gt.txt` must follow the MOTChallenge ground-truth layout expected by `mm.io.loadtxt(..., fmt="mot15-2D")`.
- There must be no header row unless the parser you use explicitly supports one.

**Extra check:** If the file has a single row, make sure your tooling still treats it as a 2D matrix. The bundled helper already normalizes single-row prediction files.

## Prediction names do not match sequence names

**Symptom:** The score is lower than expected, or only a subset of sequences appears in the summary.

**Cause:** The evaluator matches by sequence folder basename. `compare_dataframes()` only scores keys present in both dictionaries, and the helper only pairs files whose names line up.

**Fix:** Make the sequence folder name and prediction filename agree exactly:

```text
MOT17-02-FRCNN/           -> predictions/MOT17-02-FRCNN.txt
```

If you intentionally want a subset, pass `--select-sequences` and inspect the skipped list.

## Metrics are zero or unexpectedly low

**Likely causes:**

- Boxes are shifted by one pixel because `load_motchallenge()` subtracts 1 from `X` and `Y`.
- Ground-truth rows with `Confidence < 1` were filtered out.
- Your tracker is producing a different box convention than the MOTChallenge rows you are scoring.
- The matcher setting is not the one you expected. `eval_motChallenge()` uses IoU with a 0.5 threshold.

**Fix:**

1. Inspect the raw MOTChallenge rows.
2. Confirm that the prediction box format matches the expected top-left / width / height convention.
3. Verify that the ground-truth file is the labeled `train/` version.
4. Re-run the bundled smoke helper to confirm the parser and evaluator still agree on a synthetic fixture.

## The run is taking too long

**Symptom:** Full evaluation on MOT17/MOT20 takes a long time, or the helper appears to hang.

**Cause:** MOTChallenge evaluation is CPU-bound and can involve many frames and sequences. The repo's demo scripts also sit next to detector-heavy and download-heavy workflows, which can make the overall path feel expensive.

**Fix:**

- Evaluate a subset first with `--select-sequences`.
- Use the bundled smoke helper to validate the pipeline before running the full split.
- Keep external detector downloads, GPU-specific demos, and video rendering out of this sub-skill.

## You need a different tracker or video workflow

**Symptom:** The task is no longer about scoring MOTChallenge text files.

**Cause:** This sub-skill is only for MOTChallenge parsing and evaluation.

**Fix:** Route the work elsewhere:

- Tracker tuning, motion estimation, or ID switch fixes -> `tracking-core`
- Video rendering, overlays, or `VideoFromFrames` -> `video-visualization`

## The bundled smoke helper reports a dependency block

**Symptom:** `scripts/motchallenge_smoke.py` creates the fixture but stops before printing a score.

**Cause:** The fixture was created successfully, but `motmetrics` is unavailable in the active environment.

**Fix:** Install the metrics dependencies and rerun the helper. The smoke helper is intentionally honest about the block instead of pretending a score was computed.