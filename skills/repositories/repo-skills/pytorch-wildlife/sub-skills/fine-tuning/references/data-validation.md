# Fine-tuning data validation

Use this checklist before touching a trainer. It is designed for camera-trap
images and does not require model weights.

## Classification CSV

1. Read the CSV with a strict header check. Require `path`, `classification`,
   and `label`; preserve any optional `Location` and `Photo_Time` metadata.
2. Resolve each `path` against the chosen annotation/dataset root without
   silently accepting a different root. Reject absolute paths if the project
   policy requires portable annotations, or record them explicitly.
3. Check duplicate paths, unreadable files, unsupported extensions, empty
   labels, non-integer class ids, and class ids that are absent from the
   intended `[0, num_classes)` range.
4. For every class id, check that its `label` is stable. Report a conflict
   rather than choosing one spelling. Check that each split contains the
   expected class mapping after splitting.
5. Select `location` or `sequence` for camera-trap data unless there is a
   defensible reason to use random. Inspect group overlap after splitting:
   no location or 30-second sequence should occur in more than one partition.
6. For sequence metadata, parse the source spelling `Photo_Time` using
   `YYYY-MM-DD HH:MM:SS`-compatible parsing. If input uses `Photo_time`,
   normalize it explicitly and record that adaptation. Check timezone and
   clock-reset assumptions; a timestamp-only sequence key is not a substitute
   for a camera/location identifier when cameras have unsynchronized clocks.
7. Check group counts against requested proportions. A location or sequence
   split may be imbalanced or impossible when there are too few groups; report
   that limitation instead of forcing frame-level randomization.

The provided splitter writes `train_annotations.csv`,
`val_annotations.csv`, and `test_annotations.csv`. It uses a fixed seed for
random assignment unless the caller changes it, keeps grouped records
intact for location/sequence modes, and refuses to overwrite existing files
without an explicit opt-in.

## Detection tree and YAML

1. Parse YAML and require `path`, `train`, `val`, `test`, and `names` for the
   three-way layout. Confirm `names` is either a stable id-to-name list or a
   mapping accepted by the installed Ultralytics version; do not rely on
   implicit ordering.
2. Resolve the dataset root and each split path. Ensure the split paths point
   to image directories or supported source lists, not label directories.
3. For every image, derive the expected label stem and check the matching
   label directory. Report missing labels separately from intentionally empty
   negative labels.
4. Parse every non-empty label line into five fields. Validate the integer
   class id and all normalized `xywh` values: finite numbers, each in
   `[0, 1]`, and positive width/height. Reject malformed or pixel-coordinate
   annotations instead of clipping them silently.
5. Check that no source sequence or burst was copied across partitions. A
   valid YOLO file does not prove the split is statistically independent.
6. Compare YAML class count/order with every label's class ids and with the
   intended model head. A model name typo, a changed class order, or a custom
   head can invalidate otherwise valid labels.

## Configuration and device preflight

- Parse a copied YAML before invoking a launcher. Check required keys and
  values, numeric ranges, task/model choices, and that output roots are
  writable.
- Classification: verify `split_type`, sizes, `num_classes`, ResNet layer
  choice (18 or 50), batch/worker values, and logger choice. Remember that
  source code may construct a GPU accelerator even when CUDA is absent.
- Detection: verify `model` is exactly `YOLO` or `RTDETR`, `model_name` is one
  of the five supported names, and `task` is one of train/validation/inference.
  Reconcile `plot` versus the source validation branch's `plots` spelling.
- Check accelerator availability and free memory without loading a model.
  Use a local checkpoint for a smoke load; do not turn preflight into an
  implicit weight download.
- Use `workers: 0` or a small value for a first structural check if the
  launcher permits it. Increase only after file access and transforms work.

## Safe command pattern

A safe first pass is: run the splitter's `--help`, run it against a tiny CSV
with a few synthetic rows, parse the copied YAML, and inspect the emitted CSV
headers/group disjointness. Do not call a training launcher, instantiate a
pretrained model, enable Comet/W&B, or point at an external dataset merely to
validate syntax.
