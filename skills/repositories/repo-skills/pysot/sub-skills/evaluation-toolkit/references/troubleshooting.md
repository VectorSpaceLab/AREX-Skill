# Evaluation Troubleshooting

Use this when result-layout validation, evaluator imports, or full metric runs fail.

## `ModuleNotFoundError: toolkit` or `pysot`

PySOT’s packaging is unusual:

- `setup.py` installs distribution metadata for `toolkit` and builds the `toolkit.utils.region` extension.
- The `pysot` package is typically imported by running from the checkout, setting `PYTHONPATH` to the checkout root, or using an editable development install pattern.

Actionable fixes:

```bash
python -m pip install -r requirements.txt
python -m pip install "Cython<3"
python -m pip install --no-build-isolation -e .
export PYTHONPATH="$PWD:${PYTHONPATH}"
```

Do not assume a plain installed `toolkit` distribution also makes `pysot` importable from every working directory.

## `ImportError` or build failure for `toolkit.utils.region`

Signals:

- Import fails for `from toolkit.utils import region` or `from toolkit.utils.region import vot_overlap`.
- Build errors mention Cython types, `c_region.pxd`, or extension compilation.
- VOT/EAO/F1 metrics fail while parser help or simple OPE layout checks still work.

Cause and fix:

- The legacy region extension expects Cython 0.x behavior. Cython 3 can break the build.
- Install `Cython<3`, then rebuild the editable toolkit extension:

```bash
python -m pip install "Cython<3"
python -m pip install --no-build-isolation -e .
python - <<'PY'
from toolkit.utils.region import vot_overlap
print(vot_overlap([0, 0, 10, 10], [0, 0, 10, 10], (20, 20)))
PY
```

Expected overlap for identical boxes is `1.0`.

## Evaluation aborts with no trackers selected

Signals:

- The evaluation CLI raises an assertion soon after startup.
- The validator reports that `<tracker_path>/<dataset>/` is missing.
- The validator reports no directories matching the requested prefix.

Check:

```bash
find <tracker_path>/<dataset> -maxdepth 2 -type d | sort
```

Common causes:

- `--tracker_path` points at `results/<dataset>` instead of the parent `results`.
- `--dataset` spelling differs from the result directory name.
- `--tracker_prefix` is too restrictive.
- Results were written by hp-search under `hp_search_result/<dataset>/...`, but evaluation was pointed at `results`.

Fix by passing the parent result root and a prefix that matches actual tracker directory names:

```bash
python tools/eval.py --tracker_path results --dataset OTB100 --tracker_prefix siamrpn --num 1
```

## Prefix mismatch

`--tracker_prefix` is a prefix glob, not a full regular expression:

```text
<tracker_path>/<dataset>/<tracker_prefix*>
```

Examples:

- Prefix `model` matches `model`, `model_epoch20`, and `model_r255_pk-0.050...`.
- Prefix `model.pth` will not match if the tracker directory is named after the snapshot base without `.pth`.
- Empty prefix selects every tracker directory under the dataset.

Use the bundled validator first; it lists available tracker directories when a prefix selects none.

## Wrong dataset JSON or data layout

Signals:

- `FileNotFoundError` for `testing_dataset/<dataset>/<dataset>.json`.
- Image load assertions or OpenCV `None` images.
- Metric code prints tracker/video length mismatches.
- Attribute/tag key errors for LaSOT or VOT datasets.

Checklist:

1. Verify `testing_dataset/<dataset>/<dataset>.json` exists.
2. Verify the JSON entries contain the fields expected by that dataset family.
3. Verify frame image paths referenced by the JSON resolve in the current benchmark tree.
4. Verify tracker result files have one row per evaluated frame, except VOT restart markers and VOT-LT confidence handling.
5. For OTB legacy sequences, remember fallback filenames for some videos; direct `<video>.txt` remains the preferred format.

Do not “fix” metric output by truncating files blindly. If result lengths are wrong because tracking stopped early or wrote the wrong video names, route back to `../tracking-inference/`.

## Multiprocessing hangs or hard-to-read worker errors

The evaluation CLI uses `multiprocessing.Pool`. Worker exceptions can be noisy or appear after progress bars start.

Actions:

- Re-run with `--num 1` to make failures deterministic.
- Reduce tracker prefix to one tracker while debugging.
- Run the layout validator before full metric code.
- Avoid notebook or interactive multiprocessing contexts; run from a normal shell.
- If using network filesystems, copy small result fixtures locally for debugging file-discovery issues.

## Full benchmark or hp-search is not a safe smoke test

Full metric evaluation needs user benchmark assets. Hyperparameter search needs even more:

- model snapshot;
- config file;
- benchmark images and JSON sidecars;
- CUDA-capable PyTorch for the source workflow’s `.cuda()` path;
- potentially many repeated tracker runs.

Safe alternatives:

```bash
python tools/eval.py --help
python tools/hp_search.py --help
python scripts/validate_results_layout.py --help
```

Then validate a tiny synthetic result tree with the bundled script.

## Optional VOT/MATLAB integration confusion

PySOT’s Python evaluator can compute VOT-style AR/EAO and VOT2018-LT F1 from PySOT result files. Official VOT toolkit or MATLAB integration is optional and may use different configuration and workspace conventions.

Use PySOT Python evaluation for local debugging and repo-native result tables. Use official VOT tooling only when the user specifically needs official challenge submission or server-equivalent reporting.

## GOT-10k or TrackingNet scores missing

The stock Python evaluation CLI does not compute GOT-10k or TrackingNet leaderboard scores. The repo can write server-style result files, but final scoring is external to this evaluator.

Actions:

- Validate local file layout with the bundled helper for GOT-10k.
- Package results according to the benchmark server’s current instructions supplied by the user.
- Do not report PySOT Python-eval tables as official GOT-10k or TrackingNet scores.
