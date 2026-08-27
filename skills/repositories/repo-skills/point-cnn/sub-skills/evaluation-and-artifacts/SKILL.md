---
name: evaluation-and-artifacts
id: evaluation-and-artifacts
description: "Route PointCNN prediction inspection, block merging, benchmark
  metrics, and submission artifacts without training or claiming unsupported
  results."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Evaluation and artifacts

Use this sub-skill after a PointCNN segmentation inference run has produced
prediction files. It is the evaluation and observability route; it does not
train a model, prepare a dataset, download data, or repair a prediction by
changing its contents.

## When this route applies

Use it when the task is one of the following:

- preflight or audit prediction HDF5 files before a merge;
- check ShapeNet Part text labels and compute the repository-defined part IoU;
- merge S3DIS, ScanNet, or Semantic3D overlapping blocks;
- interpret a metric, submission label file, checkpoint, log, or TensorBoard
  directory produced by an already approved run.

Route upstream work instead of improvising it:

- model construction, checkpoint loading, GPU inference, and `data_num`
  production go to [segmentation-workflows](../segmentation-workflows/SKILL.md);
- raw data, HDF5 input construction, file lists, splits, and index creation go
  to [data-preparation](../data-preparation/SKILL.md).

The evaluator and merge programs used by the legacy project are external
runtime components. This skill records their observable contracts so an
operator can inspect inputs and outputs without depending on project-relative
Markdown or source paths.

## Hard runtime boundary

This is legacy TensorFlow 1.x graph-mode code. A successful TensorFlow import or
GPU device listing does not establish that segmentation can execute. All
supplied segmentation settings use FPS; the required GPU custom FPS/GatherPoint
operator is CUDA/toolchain/ABI sensitive. Current runtime evidence is:

- TensorFlow 1.15 import and device discovery passed;
- a GPU/custom-op session timed out;
- FPS is therefore `BLOCKED_REQUIRED_BACKEND`, never passed.

Do not report training, inference, or a benchmark result as passed while that
required backend gate remains blocked. CPU-only inspection of HDF5, text, NumPy,
and directory layouts is still allowed.

## Safe evaluation sequence

1. Record a run manifest before interpreting a number: dataset/version, input
   list, model and setting, checkpoint prefix, class/part map, repeat number,
   output root, and whether indices were copied from the input.
2. Run the read-only checker linked below. It only opens files and reports
   missing keys, shape/length mismatches, non-finite confidence, and basic
   index-shape/nonnegative-value violations. It never merges, writes,
   downloads, trains, or pads/truncates.

   ```bash
   python3 scripts/validate_prediction_artifacts.py --help
   python3 scripts/validate_prediction_artifacts.py --kind h5 --path PRED.h5
   # Add --index-limit N when the generic HDF5 target has N full-scene points.
   python3 scripts/validate_prediction_artifacts.py --kind s3dis --path S3DIS_PRED_ROOT
   python3 scripts/validate_prediction_artifacts.py \
     --kind shapenet --path SHAPENET_GT --pred SHAPENET_PRED
   ```

   Use `--kind semantic3d --version full|reduced` to check a Semantic3D
   result inventory. ScanNet HDF5 files use `--kind h5`; inspect the trusted
   two-object pickle separately according to the contract reference rather
   than deserializing it in this non-destructive checker. Treat errors as a
   stop condition. Resolve warnings explicitly; do not turn them into a score.
3. Read [artifact-contracts.md](references/artifact-contracts.md) for required
   keys, path layouts, valid prefixes, checkpoint boundaries, and optional PLY
   behavior.
4. Read [metrics-and-merge.md](references/metrics-and-merge.md), select exactly
   one dataset workflow, and preserve its label, confidence, tie, and index
   rules. Keep merge output in a disposable or explicitly approved destination.
5. If the preflight or evaluator fails, use
   [troubleshooting.md](references/troubleshooting.md). Re-run inference with
   the correct upstream contract rather than modifying a mismatched artifact.

## Dataset route selection

- **ShapeNet Parts:** matching category/filename text trees; subtract the
  evaluator's one global ground-truth minimum, never subtract one from
  predictions, and choose whether `--part_avg` is intended. The non-part-avg
  field printed as `IoU` is actually object point accuracy.
- **S3DIS:** validate each room's `label.npy` and indexed prediction HDF5 files,
  run the zero/half confidence merge, then evaluate `pred.npy` against the
  room labels with 13-class IoU. The evaluator reads `pred.npy` as text even
  though the filename has a NumPy suffix.
- **ScanNet:** validate `[room, point]` index pairs against the two-object
  latin-1 pickle contract, merge zero/half branches, then record point and
  voxel accuracy. The implementation uses voxel size `0.0484` and excludes
  ground-truth class 0 from denominators with the documented numerator quirk.
- **Semantic3D:** validate one of the exact `full` or `reduced` layouts, merge
  against its hard-coded scene lengths, and retain the generated one-based
  `.labels` files. Never infer a scene length from the number of blocks.

## Artifact and result boundary

A checkpoint prefix is not a prediction. Require the matching TensorFlow index
and data companions and record the model/setting and preprocessing that created
it. `ckpts/` is provenance for a run; `summary/` is an event directory for
training/validation diagnostics. TensorBoard loss, accuracy, learning-rate,
and step continuity are useful diagnostics, but they are not ShapeNet IoU,
S3DIS IoU, ScanNet accuracy, or Semantic3D submission labels.

A prediction is not a benchmark result until the input version, checkpoint,
preprocessing, class map, complete artifact inventory, evaluator output, and
warnings have been recorded. PLY files are visualization only. Missing coverage
can look like valid class 0 (or Semantic3D output label 1), so always retain
coverage and index-range observations with the metric.

## Non-goals and stop conditions

- Do not run training, inference, dataset acquisition, decompression, or a full
  benchmark as a smoke test from this route.
- Do not merge when required HDF5 datasets, indices, valid lengths, label ranges,
  room/category files, or expected scene artifacts are missing.
- Do not resolve a length mismatch by padding or truncating.
- Do not silently treat a missing branch, zero confidence, untouched index, or
  empty class union as a valid prediction.
- Do not call FPS `passed`; the current required-backend evidence remains
  `BLOCKED_REQUIRED_BACKEND`.

## Bundled tool and references

- [validate_prediction_artifacts.py](scripts/validate_prediction_artifacts.py):
  read-only HDF5, text, NumPy, and Semantic3D-inventory preflight; it never
  deserializes a pickle.
- [metrics-and-merge.md](references/metrics-and-merge.md): formulas, label
  offsets, branch merge rules, scene tables, and output names.
- [artifact-contracts.md](references/artifact-contracts.md): input/output
  schemas and checkpoint/log/summary boundaries.
- [troubleshooting.md](references/troubleshooting.md): failure classification
  and recovery without mutating artifacts.
