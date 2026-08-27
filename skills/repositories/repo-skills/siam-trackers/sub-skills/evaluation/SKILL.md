---
name: evaluation
description: "Test NanoTrack-compatible trackers on named datasets, validate
  result layouts, dispatch benchmark protocols, interpret tracking metrics, and
  plan bounded hyperparameter searches."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# NanoTrack Evaluation

Use this sub-skill to plan or diagnose NanoTrack benchmark testing, validate
already-produced result files, choose the matching evaluator, interpret metrics,
or bound a hyperparameter search. NanoTrack is the collection's maintained
workflow; treat other tracker snapshots as catalogue entries unless explicitly
routed elsewhere.

## Route First

- Model/config/checkpoint loading, device placement, tracker initialization, or
  frame-by-frame prediction: route to
  [inference](../inference/SKILL.md).
- Dataset cropping, losses, optimization, checkpoint creation, or resume: route
  to [training](../training/SKILL.md).
- ONNX/NCNN conversion, FLOPs, latency, or deployment speed claims: route to
  [export](../export/SKILL.md).
- Any non-NanoTrack snapshot or comparison across snapshots: route to
  [variant-catalog](../variant-catalog/SKILL.md).

Do not convert an evaluation request into training, and do not treat benchmark
speed output as a controlled export/deployment benchmark.

## Read By Need

- Dataset names, factory behavior, on-disk data assumptions, CLI flag contracts,
  and exact result paths: [datasets and results](references/datasets-and-results.md)
- Evaluator dispatch, metric meaning, GOT-10k wrappers, and bounded parameter
  search: [benchmarks](references/benchmarks.md)
- Extension ABI, imports, data/path mismatches, workers, GUI, CUDA, and known
  dispatch defects: [troubleshooting](references/troubleshooting.md)
- Offline structural preflight:
  [`check_result_layout.py`](scripts/check_result_layout.py)

## Hard Gates

A full run is not self-contained in this skill. Establish all of these before
claiming test or evaluation success:

1. The named dataset and its annotations/images are present in the layout
   expected by the selected wrapper.
2. A matching NanoTrack config and checkpoint exist; evaluation-only work may
   instead start from complete result files.
3. The model runtime can import its dependencies and, for stock testing, use an
   explicitly selected CUDA device. A merely visible GPU is not proof it is
   free or compatible.
4. The Cython extension exposing `toolkit.utils.region` was built for the active
   Python ABI. Never accept a copied prebuilt `region.so` as proof.
5. The result root, dataset name, and tracker name resolve to the same directory
   contract for result production and result consumption.
6. Multiprocessing and any plotting/visualization requirements are acceptable
   for the host. Use a headless path unless visualization was requested.

No dataset or checkpoint is bundled. Full tracking, training, benchmark,
parameter-search, plotting, and export execution were not verified during skill
construction. Never invent scores or imply that a layout-only pass validates
tracking quality.

## Operating Sequence

### 1. Normalize the request

Record:

- test-and-evaluate, evaluate-existing-results, layout-only, or hyperparameter
  search;
- exact dataset spelling and protocol;
- dataset root, result root, tracker name/pattern, and expected sequences;
- config/checkpoint pair and GPU allocation when predictions must be produced;
- required metrics, worker limit, visualization policy, and completion proof.

If the user asks for a single video, remember that result production may filter
to it while the evaluator still expects a complete dataset unless separately
constrained. Prefer layout validation over launching a full evaluator on partial
results.

### 2. Select dataset and protocol

Use `DatasetFactory.create_dataset(name, dataset_root, load_img=False)` for the
maintained test-side contract. `load_img=False` avoids caching every image, but
wrappers still open frames while iterating and some inspect the first image at
construction. It is not a metadata-only mode.

Choose one protocol:

- OPE: OTB, DTB70, UAVDT, VisDrone, LaSOT, UAV123/UAV20L, or NFS.
- GOT-10k validation/reporting: `GOT-10k`.
- VOT restart: VOT2016, VOT2017, VOT2018, or VOT2019.
- VOT long-term: VOT2018-LT.

Read the dispatch asymmetries before launch: VOT2017 is evaluator-only in this
snapshot; TrackingNet is factory-only; UAVDT and VisDrone need an evaluator
import correction in an active runtime.

### 3. Separate production from evaluation

Result production consumes images, config, checkpoint, tracker code, OpenCV,
PyTorch, and CUDA. Evaluation consumes images/annotations plus result files and
may start process pools. Keep their evidence distinct:

- a result file exists: production wrote something;
- bundled validator passes: names, row types, and selected counts are coherent;
- evaluator completes: protocol code consumed data and results;
- metric is credible: protocol, dataset split, result completeness, and runtime
  were documented.

### 4. Validate result files offline

Run the bundled standard-library checker before importing the evaluation stack:

```bash
SKILL_DIR=/path/to/evaluation
python "$SKILL_DIR/scripts/check_result_layout.py" --list-datasets
python "$SKILL_DIR/scripts/check_result_layout.py" \
  --dataset OTB100 --results-root ./results --tracker-name nanotrack \
  --sequence FleetFace:707
```

For VOT restart, the default check enforces the stock loss/restart marker
schedule. Use `--relax-vot-restart` only when deliberately validating a
non-stock but protocol-compatible producer. Add `--json` for machine-readable
output. The checker performs no downloads, imports, multiprocessing, metrics,
or GUI work.

### 5. Evaluate with the matching benchmark

- OPE: success curve/AUC and 20-pixel precision; LaSOT additionally reports
  normalized precision at threshold 0.20.
- VOT restart: accuracy, robustness/lost count, and EAO.
- VOT2018-LT: confidence-threshold precision, recall, and maximum F1.
- GOT-10k validation: AO, success rate at IoU greater than 0.5, and speed from
  positive timing rows.

Interpret only metrics actually emitted. Do not compare numbers across different
protocols as if they had the same denominator or restart behavior. Read
[benchmarks](references/benchmarks.md) before explaining metric trade-offs.

### 6. Search hyperparameters safely

Search only after one fixed configuration produces valid results and metrics.
Freeze dataset split, checkpoint, variant, device policy, and evaluator. Compute
the Cartesian trial count before launch, use a small coarse grid, allocate a
unique result directory per trial, and never treat an `Occ` placeholder as a
completed result. Select on a validation set; reserve test/hidden-test results
for final reporting. Record the full tuple `(penalty_k, lr,
window_influence, instance_size)` with every score.

## Completion Evidence

Return a concise record containing:

- exact dataset/protocol and whether results were produced or only inspected;
- data, checkpoint, CUDA, extension, worker, and GUI gate status;
- result-root/dataset/tracker path contract;
- validator command and exit status;
- evaluator class and emitted metric names, with scores only when truly run;
- missing sequences/files, warnings, patches, and unresolved limitations.
