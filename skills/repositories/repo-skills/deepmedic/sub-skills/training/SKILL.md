---
name: training
description: "Author DeepMedic 0.8.4 training configurations, launch CPU/GPU
  training, resume or fine-tune checkpoints, and inspect metrics and outputs
  safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# DeepMedic training

Use this skill when the task is to configure or operate a DeepMedic 0.8.4
training session. The canonical training entry point is `deepMedicRun`; this
skill covers the training session, not model architecture authoring, raw NIFTI
preparation, or test-only inference.

## Operating boundary

- **Training is expensive.** A full 3-D DeepMedic run can take hours or days
  and consumes substantial CPU/GPU memory. Start with a tiny configuration,
  one or a few cases, one or two epochs, few subepochs, and a small segment
  count as a smoke test. Only then scale to production values.
- The verified runtime is Python 3.8.20, TensorFlow 2.6.2, NumPy 1.19.5,
  SciPy 1.7.3, pandas 1.2.5, NiBabel 3.2.2, matplotlib 3.5.3, and protobuf
  3.20.3. The package imports successfully and both `deepMedicRun -h` and the
  progress plotter help path exit successfully. TensorFlow is not declared by
  `setup.py`, so install and verify it separately in the runtime environment.
- The tested TensorFlow CUDA build is 11.2 and sees eight A100 GPUs (compute
  capability 8.0). This is evidence about the verified environment, not a
  requirement that every deployment have these GPUs. A GPU deployment must
  still use a TensorFlow/CUDA/cuDNN combination compatible with its host.
- Input images, labels, and optional masks must already be valid, co-registered
  NIFTI data. Follow [data preparation](../data-preparation/SKILL.md). For
  downstream segmentation or test-only output semantics, use
  [inference](../inference/SKILL.md).

## Fast routing checklist

1. Confirm the model configuration and its number of output classes. Labels
   include background class `0` and use contiguous class ids.
2. Create a Python-syntax train config. At minimum, provide
   `folderForOutput`, `channelsTraining`, `gtLabelsTraining`, and
   `batchsize_train`; `sessionName` is strongly recommended. Paths in a train
   config are interpreted relative to the config file, not the caller's
   current directory.
3. Decide CPU versus GPU explicitly. Use `-dev cpu` for a small smoke test;
   use `-dev cuda` for TensorFlow's visible GPUs or `-dev cudaN` to select one
   numbered host GPU. See [workflows](references/workflows.md).
4. Run a smoke test before enabling validation, affine augmentation,
   multiprocessing, full-volume validation, or a large segment budget.
5. Inspect the read-only output report from
   `scripts/check_training_outputs.py`, then inspect the text log. Plot with
   `scripts/plot_training_progress.py` or enable TensorBoard.
6. For continuation, load a complete checkpoint prefix. For fine-tuning a
   pretrained network with a fresh schedule, add `-resetopt`; this preserves
   network weights but resets the trainer and optimizer state.

## CLI contract

The training invocation has this shape (the executable must be available in
PATH):

```text
deepMedicRun -model MODEL_CFG -train TRAIN_CFG [-load CHECKPOINT_PREFIX] [-resetopt] [-dev cpu|cuda|cudaN]
```

- `-model` is required by the front end and points to the architecture config.
- `-train` selects training and must follow `-model` conceptually; it points
  to the Python-syntax train config.
- `-load` is optional and overrides `cnnModelFilePath` in the train config.
  It accepts a TensorFlow checkpoint **prefix**, not an individual shard.
- `-resetopt` is only valid with `-train` and `-load`/a configured checkpoint.
  It reinitializes trainer variables while retaining trainable `net/*`
  variables.
- `-dev cpu` sets `CUDA_VISIBLE_DEVICES` empty and binds the graph to
  `/CPU:0`. `-dev cuda` leaves CUDA devices visible and lets TensorFlow choose
  the available GPU. `-dev cudaN` masks to host GPU `N` and binds the process'
  visible GPU 0. An invalid device string is rejected.

Use `deepMedicRun -h` before a run to verify the installed entry point. GPU
selection is not proof of GPU execution: check the session log's device list
and the host's accelerator monitor, and treat CUDA/cuDNN initialization errors
as a backend failure rather than silently trusting the requested flag.

## Data contract at the training boundary

The direct file-list form is:

- `channelsTraining`: a Python list with one file-list path per input
  modality. Every list file has one NIFTI path per case; all modality lists
  must have the same number and order of cases.
- `gtLabelsTraining`: one file-list path containing one label NIFTI per case.
  It is required for supervised training. Labels are integer-like and must be
  in `[0, numberOfOutputClasses - 1]`.
- `roiMasksTraining`: optional file-list path, one mask per case. With a mask,
  sampling is restricted to positive-mask voxels; without one, the full volume
  is eligible according to the sampling type.

The current parser also supports `dataframe_train`: a CSV with alphabetically
sorted `channel_*` columns and a required `ground_truth` column (optional
`roi_mask`). If it is supplied, it is used instead of the three direct
training lists. Keep this alternative explicit; do not mix it accidentally
with stale direct-list settings.

Validation is disabled by default. If either
`performValidationOnSamplesThroughoutTraining` or
`performFullInferenceOnValidationImagesEveryFewEpochs` is true, provide
`channelsValidation`; provide `gtLabelsValidation` for sample validation and
for validation metrics; provide `roiMasksValidation` only when available. Full
validation output needs `namesForPredictionsPerCaseVal` when segmentation,
probability maps, or feature maps are saved. Names are case names, not paths.

## What happens in one run

The session creates the output tree, builds the TensorFlow graph, initializes
or restores variables, then repeats epochs and subepochs. Each subepoch samples
cases and patches, validates first when requested, trains in complete batches,
and reports metrics. At epoch end it updates the schedule, increments the
saved epoch counter, saves a checkpoint, and optionally performs full-volume
validation. At normal completion it writes a final checkpoint. Sampling can be
sequential (`num_processes_sampling = -1` or default thread behavior `0`) or
parallel (`>0` child processes); begin with `-1`/`0` when diagnosing failures.

`numberTrainingSegmentsLoadedOnGpuPerSubep` is a sample budget, not a batch
count. The routine computes optimization batches as the number of extracted
segments integer-divided by `batchsize_train`; leftover segments are ignored.
Keep the segment budget divisible by the batch size to avoid an unexpectedly
short subepoch. `numberOfSubepochs` controls metric reports and fresh sampling,
while `numberOfEpochs` is the training-state stopping target.

## Checkpoint, resume, and fine-tune rules

TensorFlow writes a checkpoint set such as:

```text
<model>.<session>.<timestamp>.model.ckpt.index
<model>.<session>.<timestamp>.model.ckpt.data-00000-of-00001
```

The value passed to `-load` or `cnnModelFilePath` must be the shared prefix
ending exactly in `.model.ckpt`, **not** the `.index` file and not the
`.data-...` shard. A complete checkpoint set is required. Use the same model
architecture config when resuming; variable-name or shape mismatches indicate
a different architecture or incompatible checkpoint.

- **Resume interrupted training:** load an epoch checkpoint without
  `-resetopt`. The network, optimizer accumulators, current schedule state, and
  saved `num_epochs_trained` are restored. Training continues until the
  configured total epoch count is reached; if the checkpoint already reached
  that count, no training epoch runs.
- **Fine-tune:** use the matching architecture and `-load` a pretrained
  prefix, usually with `-resetopt`. This restores only network weights and
  initializes optimizer variables, epoch counter, and schedule state from the
  new config. It does not reinitialize trainable network weights.
- **Freeze selected layers:** `layersToFreezeNormal`,
  `layersToFreezeSubsampled`, and `layersToFreezeFC` are one-based config layer
  numbers. The implementation converts them to zero-based internal indices;
  an omitted subsampled list mirrors the normal list.

Do not delete or overwrite a checkpoint while a run is active. The supplied
output checker is read-only and can identify usable prefixes.

## Metrics and progress

Each session log is `<folderForOutput>/logs/<sessionName>.txt`. Training and
sample-validation metrics are reported per subepoch and epoch. Class `0` is
reported as merged foreground in the accuracy monitor (not as ordinary
background); class-specific reports for other classes are one-vs-all. Full
validation Dice is computed from whole-volume inference and is distinct from
sample Dice.

With `tensorboard_log = True`, TensorBoard event files are placed below
`<folderForOutput>/tensorboard/<sessionName>/train` and `/val`. The logger
records sample accuracy/cost and per-class accuracy, sensitivity, precision,
specificity, and Dice; full-volume validation records Dice1, Dice2, and Dice3.
TensorBoard files are binary and are not a substitute for the text log.

Use the bundled plotter with explicit log paths, for example:

```text
python sub-skills/training/scripts/plot_training_progress.py LOG.txt --detailed --moving-average 20 --save-figure --output-dir PLOTS
```

The plotter parses only known DeepMedic log sentences, carries forward `N/A`
metric values as the original utility does, smooths sample metrics but not
full-volume Dice, and never evaluates log content as Python. `--help` documents
all flags. Use `--no-show` in headless jobs. Basic mode plots overall accuracy;
detailed mode supports `--classes` and plots validation/training accuracy,
sensitivity, precision, sample Dice, and validation full-volume Dice.

## Handoff

For the long config matrix, schedule behavior, augmentation dictionaries,
output layout, and failure diagnosis, read the linked files:

- [train-config.md](references/train-config.md)
- [workflows.md](references/workflows.md)
- [troubleshooting.md](references/troubleshooting.md)

Run the two bundled scripts with `--help`; they are safe wrappers and do not
modify training outputs. A successful parser/help check is not a successful
training run: verify the log reaches session completion and that checkpoint
prefixes and expected prediction/event folders exist.
