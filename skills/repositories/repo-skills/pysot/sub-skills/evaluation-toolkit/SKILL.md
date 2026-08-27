---
name: evaluation-toolkit
description: "Evaluate PySOT benchmark result layouts, metric families, eval
  commands, hp_search, and dataset adapter troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Evaluation Toolkit

Use this sub-skill when the task is about evaluating already-generated PySOT tracker results, checking benchmark result layouts, selecting the metric family, running the PySOT evaluation CLI, interpreting OPE/AR/EAO/F1 output, using hyperparameter-search result conventions, or debugging dataset/result adapter failures.

## Route here for

- “Evaluate PySOT results” or “run eval.py” on OTB, UAV, NFS, LaSOT, VOT short-term, or VOT2018-LT style outputs.
- Result-tree questions such as tracker directory names, per-video result files, VOT `baseline/` or `longterm/` folders, GOT-10k server-style files, or `--tracker_prefix` matching.
- Metric-family questions: OPE success/precision/norm precision, VOT accuracy/robustness/EAO, and VOT-LT precision/recall/F1.
- Safe preflight checks that do not require benchmark images, snapshots, CUDA, or full metric computation.
- Hyperparameter-search planning and result naming for penalty-k, learning rate, window influence, and search-region sweeps.

## Route elsewhere

- To generate tracker result files from snapshots/videos/datasets, use sibling sub-skill `../tracking-inference/`.
- To train a snapshot or prepare training crops/annotations, use sibling sub-skill `../training-data/`.
- To choose or edit model/config families before running tracking, use sibling sub-skill `../configuration-models/`.
- For cross-cutting install/import issues before any workflow, use the root skill troubleshooting and environment checks.

## Operating workflow

1. Identify the benchmark family and result root.
   - PySOT’s evaluation CLI expects a tracker root shaped like `<tracker_path>/<dataset>/<tracker_name>/...`.
   - The default tracker root from PySOT tracking runs is usually `results/`.
   - Full metric evaluation also expects benchmark data and JSON sidecars under `testing_dataset/<dataset>/`; the bundled validator below only checks result-tree shape.
2. Read [references/datasets-and-results.md](references/datasets-and-results.md) for supported dataset names, JSON sidecars, and expected tracker result files.
3. Run the safe validator before full evaluation:

   ```bash
   python scripts/validate_results_layout.py \
     --tracker-path results \
     --dataset OTB100 \
     --tracker-prefix siamrpn
   ```

   This does not import PySOT, open images, require CUDA, or compute metrics. It fails clearly when the dataset result directory or prefix-selected tracker directories are missing, and it prints an evaluation command skeleton when PySOT’s Python evaluator supports the dataset family.
4. Read [references/metrics.md](references/metrics.md) to map the dataset family to `OPEBenchmark`, `AccuracyRobustnessBenchmark`, `EAOBenchmark`, or `F1Benchmark` and to interpret printed columns.
5. Read [references/workflows.md](references/workflows.md) for concrete `eval` and `hp_search` command templates, flag semantics, and VOT/server benchmark notes.
6. If validation or evaluation fails, use [references/troubleshooting.md](references/troubleshooting.md) before changing code. Common fixes are prefix correction, moving result directories under the expected dataset root, installing the legacy `toolkit.utils.region` extension with `Cython<3`, and reducing multiprocessing to `--num 1`.

## Safe versus full checks

Safe checks in this sub-skill:

- CLI help/import checks for the evaluation and hyperparameter-search scripts.
- Import of benchmark classes and the region extension after the toolkit is installed.
- Result-tree validation with the bundled script.
- Small synthetic result-layout fixtures.

Full metric evaluation is not a safe default check. It requires user-supplied benchmark datasets, JSON sidecars, tracker result files, and a compatible Python environment. Hyperparameter search additionally requires a model snapshot, PySOT config, benchmark images, and CUDA because the source workflow loads the model with `.cuda()`.

## Input/output contract

Inputs usually needed:

- `tracker_path`: root containing dataset result directories, for example `results`.
- `dataset`: one of the supported dataset family names described in the references.
- `tracker_prefix`: optional prefix used to select tracker directories under `<tracker_path>/<dataset>/`.
- For full evaluation only: benchmark data at `testing_dataset/<dataset>/` with `<dataset>.json` sidecar and image/ground-truth files referenced by the sidecar.

Outputs:

- Validator: actionable pass/fail report and an evaluation command skeleton.
- PySOT evaluation: terminal tables for success/precision/norm precision, accuracy/robustness/lost/EAO, or precision/recall/F1 depending on dataset family.
- Hyperparameter search: many tracker result directories named from snapshot and parameter values under the hp-search result root; evaluate or compare them like ordinary tracker directories after the expensive sweep finishes.
