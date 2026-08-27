---
name: inference
description: "Run and validate DeepMedic 0.8.4 whole-volume inference from a
  compatible model checkpoint and NIFTI inputs, including TestConfig authoring,
  tiling, ROI restriction, probability/feature outputs, and DSC reporting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# DeepMedic inference

Use this skill when a trained DeepMedic network must segment unseen, co-registered
NIFTI volumes or when an inference result needs a deterministic output check.
This is an operating guide for the installed DeepMedic 0.8.4 package. It does
not create a network architecture or a raw-data manifest. For those tasks use
[the model-architecture skill](../model-architecture/SKILL.md) and [the
data-preparation skill](../data-preparation/SKILL.md).

## Fast route

1. Confirm that the model configuration describes **the exact architecture used
   to make the checkpoint**: input-channel count, class count, pathway choices,
   layer/kernel definitions, subsampling factors, and inference segment size.
2. Create a test configuration with a writable output folder, one channel list
   per model input channel, and one output name per case. Add ROI and labels
   only when their files exist and are shape-compatible.
3. Run the installed CLI with `-model`, `-test`, and either `-load` or
   `cnnModelFilePath`. Select `-dev cpu`, `-dev cuda`, or `-dev cudaN` after
   checking the TensorFlow/CUDA installation.
4. Check the session log and validate every expected output with
   `scripts/check_inference_outputs.py`. Inspect NIFTI shape, affine, dtype,
   finite values, class probabilities, and ROI behavior before consuming a
   result downstream.

Read [test-config.md](references/test-config.md) for the configuration contract,
[workflows.md](references/workflows.md) for the complete run and validation
sequence, and [troubleshooting.md](references/troubleshooting.md) when a run
fails.

## Preconditions and boundaries

- Inputs are NIFTI volumes (`.nii` or `.nii.gz`). Each case's modalities,
  optional label, and optional ROI must be co-registered and have identical
  voxel dimensions. The dataset should use a consistent voxel size across
  cases; labels use background `0` and consecutive class IDs.
- The number and order of channel list files must match the model's input
  channel count. A `-` line in a channel list deliberately creates a zero-filled
  channel; use it only when that modality is intentionally absent.
- A checkpoint is a TensorFlow checkpoint **prefix**, conventionally ending in
  `.model.ckpt`, not the `.data-*`, `.index`, or `.meta` companion file. A
  directory is also accepted; DeepMedic asks TensorFlow for its latest
  checkpoint.
- Do not use a checkpoint with a different architecture. TensorFlow restore
  errors are commonly caused by variable/name/shape mismatch, not by bad NIFTI
  data. Reuse the model configuration that produced the checkpoint.
- A feature-map request is optional and can consume many times more disk and
  memory than segmentation. Request narrow layer/range slices first.

## TestConfig contract

`TestConfig(abs_path_to_cfg)` executes the configuration as Python and exposes
its variables through the `Config` interface. Therefore use ordinary Python
syntax, keep the file trusted, and make all paths either absolute or relative
to the test-config file (except the command-line `-load` path, which is first
resolved relative to the process working directory).

Required for the legacy list-file input path:

- `folderForOutput`: writable main output directory.
- `channels`: list of channel-list files, one per model input channel.
- `namesForPredictionsPerCase`: a list file with exactly one safe output name
  per case. Use names that do not contain `/` or begin with `.` (the source
  includes this convention helper, though the current test-session path does
  not invoke it consistently). The name may be a basename, a `.nii`, or a
  `.nii.gz` name; DeepMedic appends the configured suffix.

`sessionName` is strongly recommended; its default is `testSession`. A missing
checkpoint is not silently safe: the CLI asks whether to test a randomly
initialized model, and non-interactive runs should decline by supplying a
checkpoint instead.

The v0.8.4 parser also accepts `dataframe`, where pandas reads a CSV and sorts
columns beginning with `channel_` alphabetically. Optional columns are
`ground_truth`, `roi_mask`, and `prediction_filename`. When `dataframe` is
used, those paths replace the legacy lists; `prediction_filename` supplies
output names. Keep the legacy `channels` plus names lists when portability and
explicit ordering matter. See [test-config.md](references/test-config.md) for
all defaults and invariants.

## CLI and precedence

The normal form is:

```text
deepMedicRun -model MODEL_CFG -test TEST_CFG [-load CHECKPOINT] [-dev cpu|cuda|cudaN]
```

`-model` is required by the top-level CLI and must be supplied even when
`TEST_CFG` contains the checkpoint. `-test` selects inference and cannot be
combined with `-train`. `-load` is valid with `-test` or `-train`; for testing,
it overrides `cnnModelFilePath` in the test configuration. The override is
absolute-resolved from the current working directory, while a model path read
from the config is resolved relative to that config file. Put the prefix, not a
checkpoint shard, in either location.

`-dev cpu` is the default and clears visible CUDA devices before creating the
TensorFlow graph. `-dev cuda` lets TensorFlow see its available GPUs and uses
the first suitable device. `-dev cudaN` exposes only GPU N and binds the graph
to GPU 0 in the masked view. A requested GPU must be visible to the installed
TensorFlow build and have compatible CUDA/cuDNN libraries; otherwise use CPU
for a small smoke test or fix the runtime rather than assuming silent GPU use.
The verified production environment for this skill was Python 3.8.20,
TensorFlow 2.6.2, NumPy 1.19.5, and a CUDA TensorFlow build seeing A100 GPUs,
but this is evidence for the packaged revision, not a universal hardware
requirement.

## What a successful run does

For each case DeepMedic loads all channels, optionally labels and an ROI,
performs input checks, pads to cover the receptive field when
`padInputImagesBool=True`, and applies the configured z-score normalization.
It computes the normal-path output dimensions and tiles the padded volume. The
tiling stride equals the number of central voxels predicted by one forward
pass. Tiles are stitched into full-volume class probability arrays; argmax
across classes produces the segmentation. ROI tiles with no positive voxel are
skipped. After inference, padding is removed, then the segmentation and every
probability map are multiplied by the unpadded ROI when an ROI was supplied.
Thus ROI restriction affects both work and saved outputs; it is not merely an
evaluation crop.

The session creates a main output tree containing logs and, under the session's
prediction result, separate `predictions/` and `features/` directories. For an
output name `caseA.nii.gz` and default suffixes, expect:

- `caseA_Segm.nii.gz` for the integer segmentation (if enabled).
- `caseA_ProbMapClass0.nii.gz`, `caseA_ProbMapClass1.nii.gz`, etc. for enabled
  class probabilities.
- `caseA_pathwayP_layerL_fmF.nii.gz` in `features/` for each selected feature
  map, where pathway, layer, and FM indices are zero-based.

The first input channel is used as the NIFTI affine/header source. Validate
that its affine and shape represent the intended case. DeepMedic saves
segmentation as int16 and probabilities/features as float32.

If labels are supplied, DeepMedic reports per-case and mean DSC. `calculate_dice`
uses `2 * sum(prediction * ground_truth) / (sum(prediction) + sum(ground_truth))`;
when the ground-truth foreground is empty it returns `-1`, which is rendered as
an NA marker. For each class report there are three values: DICE1 compares the
whole-volume prediction to whole-volume GT; DICE2 compares the prediction
masked to the ROI against whole GT; DICE3 compares both prediction and GT
inside the ROI. Class 0 means merged foreground (`label > 0`), not background.
Consult DICE2/DICE3 when an ROI was part of the intended task.

## Output acceptance gate

Do not call a run complete merely because the process exits. Confirm all of the
following:

- The log says parameters loaded from the intended checkpoint and the expected
  number of cases was processed; no random-initialization prompt was accepted.
- Every expected segmentation and enabled class probability exists. Use the
  bundled checker for presence checks without modifying data:

  ```text
  python scripts/check_inference_outputs.py PREDICTIONS_DIR caseA caseB --prob-classes 3 --require-features --feature-dir FEATURES_DIR
  ```

  The checker accepts case names with or without NIFTI extensions, reports all
  missing files, and exits nonzero on missing requested outputs. It performs a
  safe synthetic-directory check with `--self-test`; no NIFTI or checkpoint is
  needed for that check.
- NIFTI files have the expected spatial shape and affine, segmentation labels
  are integral and within `[0, numberOfOutputClasses - 1]`, and probability
  maps are finite. Probability maps should be nonnegative and sum approximately
  to one over predicted voxels before any intentional ROI zeroing.
- Outside a supplied ROI, saved segmentation and probability values are zero.
  If `padInputImagesBool=True`, saved dimensions should return to the original
  unpadded dimensions.
- If labels were supplied, record the per-case and mean DSC from the log and
  distinguish NA (empty GT foreground) from a numerical zero.
- Feature-map presence is checked only when requested, and selected ranges are
  checked against the model's layer counts. Saving all maps indiscriminately is
  a storage and RAM hazard.

For a successful run, hand the output directory, checkpoint prefix, model
configuration identity, test configuration, device selection, ROI choice,
normalization settings, and checker report to the next pipeline stage. Keep
this inference skill focused: architecture creation belongs to
`../model-architecture/SKILL.md`, and channel/ROI/label file preparation
belongs to `../data-preparation/SKILL.md`.
