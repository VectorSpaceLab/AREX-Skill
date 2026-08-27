---
name: analysis-and-packaging
description: "Analyze saved PyTracking tracking/VOS results, plan plots, package
  GOT-10k and TrackingNet submissions safely, handle raw result archives, and
  plan VOT integration."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# Analysis and Packaging

Use this sub-skill when a task starts from **already saved PyTracking results** and asks for analysis, plots, result-file diagnosis, VOS mask evaluation, GOT-10k or TrackingNet submission packaging, raw-result archive handling, or VOT integration planning.

Do **not** use this sub-skill to run trackers or train models. Route tracker/video/dataset execution to `tracking-evaluation`; route LTR training, checkpoints created by training, and training-setting edits to `ltr-training`.

## Fast routing

- Need to score/plot bounding-box results, inspect `eval_data.pkl`, replay saved boxes, or translate an analysis notebook into a script: read [references/analysis-api.md](references/analysis-api.md).
- Need to package GOT-10k or TrackingNet outputs, check expected result trees, reason about raw result downloads/unpacking, or plan VOT toolkit integration: read [references/vot-and-result-packaging.md](references/vot-and-result-packaging.md).
- Need symptom-to-fix guidance for missing result files, run-id naming, plotting backends, VOS masks, VOT TraX, or package submission layout: read [references/troubleshooting.md](references/troubleshooting.md).
- Need a safe dry-run packaging check without creating archives: use [scripts/plan_result_packaging.py](scripts/plan_result_packaging.py).

## Operating assumptions

1. A PyTracking checkout or installed package is already usable in the user's environment.
2. The user's local PyTracking configuration points result analysis to writable `results_path`, `result_plot_path`, and, for official submissions, packed-result output roots.
3. Saved box results use one row per frame with `[top_left_x, top_left_y, width, height]`, read from comma- or tab-delimited text files.
4. Saved VOS results are indexed mask images laid out by sequence name under each tracker's segmentation result directory.
5. Official benchmark uploads are strict about file names and directory layout; plan and validate before creating zips.

## Typical workflows

### Score or plot saved bounding-box results

1. Build tracker objects with `trackerlist(name, parameter_name, run_ids=None, display_name=None)`.
2. Build a dataset with `get_dataset(...)` using a known PyTracking dataset alias.
3. Call `print_results(...)` for tables or `plot_results(...)` for PDF plots.
4. If multiple stochastic runs were evaluated, pass `merge_results=True` only when those runs represent repeat trials of the same tracker/parameter pair.
5. If plotting in a headless session, set a non-interactive Matplotlib backend before importing plotting code.

### Evaluate VOS masks

1. Use tracker objects whose `segmentation_dir` points to saved masks.
2. Use `evaluate_vos(trackers, dataset='yt2019_jjval', force=False)` for J-Mean/J-Recall/J-Decay reports.
3. Confirm mask file names match the dataset annotation frame names and object ids are encoded as indexed mask labels.

### Plan an official result package

Use the bundled planner first. It does not import PyTracking, run trackers, download data, or write archives by default.

```bash
# From this sub-skill directory, or with the bundled script path resolved explicitly:
python scripts/plan_result_packaging.py \
  got10k --tracker-name dimp --parameter-name dimp50 --results-root /path/to/results

python scripts/plan_result_packaging.py \
  trackingnet --tracker-name dimp --parameter-name dimp50 --run-id 0 \
  --results-root /path/to/results --trackingnet-sequence-list trackingnet_test_sequences.txt
```

Create archives only after the plan reports the expected tree and no blocking missing files.

## Guardrails

- Do not download raw benchmark results, unpack archives over an existing result root, or create official zips unless the user explicitly asks and the target paths are clear.
- Do not treat a partial result tree as upload-ready. GOT-10k test packaging expects 180 test sequences and three run ids (`000`, `001`, `002`). TrackingNet completeness should be checked against a known sequence list or the PyTracking dataset registry.
- Do not link future runtime instructions to the source checkout. If a helper is needed, use the bundled script in this sub-skill.
- VOT integration requires external toolkit/TraX setup. Plan the configuration first; do not assume the Python wrapper, MATLAB toolkit, or native TraX libraries are present.
