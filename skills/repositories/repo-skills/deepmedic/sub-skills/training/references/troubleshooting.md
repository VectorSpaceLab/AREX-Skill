# Training troubleshooting

Use the session log first, then the read-only output checker. Classify a
failure before changing several settings at once. Keep the last usable
checkpoint; a partial log is not proof that the network weights were saved.

## CLI and environment

**`deepMedicRun -h` fails or import errors appear**

- Confirm the installed package is the intended DeepMedic 0.8.4 build.
- Verify Python, TensorFlow, NumPy, SciPy, pandas, NiBabel, matplotlib, and
  protobuf versions are mutually compatible. `setup.py` does not declare
  TensorFlow, so a successful package install alone is insufficient.
- Run the bundled help checks before attempting a model graph. Do not diagnose
  NIFTI or CUDA until import and CLI parsing work.

**`-dev` is rejected**

Only `cpu`, `cuda`, or `cuda` followed by an integer are accepted. Spell
`cuda0`, not `gpu0`. `-resetopt` must accompany training, not test mode.

**GPU request runs on CPU or fails in CUDA initialization**

The front end treats `cuda` as all visible GPUs and `cudaN` as a masked host
GPU. Check TensorFlow's device listing in the log and the host accelerator
monitor. Then verify the TensorFlow/CUDA/cuDNN/driver combination and library
visibility in the environment. A warning about no device, cuInit, or missing
CUDA libraries is a backend problem; reducing the model does not fix it.
Use `-dev cpu` only as a diagnostic or tiny smoke fallback, not as evidence
that the GPU stack is correct.

## Config parsing and required inputs

**`channelsTraining` or `gtLabelsTraining` required-element error**

The direct-list form needs both keys. `channelsTraining` must be a Python list
with one file-list path per modality. `gtLabelsTraining` is one file-list path.
If using `dataframe_train`, verify the CSV has sorted `channel_*` columns and a
`ground_truth` column, and do not rely on stale direct-list paths. A path is
resolved relative to the train config; a path inside a file list is resolved
relative to that list file.

**Case-count mismatch or missing file**

Count non-comment, non-blank entries in every channel, label, ROI, weight-map,
and validation list. They must describe the same cases in the same order. The
special channel line `-` means a zero-filled modality, not a filesystem path.
Check spelling, permissions, and NIFTI suffixes. Keep raw preparation outside
this skill and follow the data-preparation skill for shape/registration issues.

**`TrainConfig(abs_path_to_cfg)` appears to execute unexpected content**

Train configs are executed as Python source by design. Keep them declarative:
literals and comments only. Do not paste shell commands, untrusted Python, or
values copied from a different DeepMedic version. The bundled progress plotter
is deliberately safer: it parses known text patterns and does not execute log
content.

**Auto schedule complains about validation**

`typeOfLearningRateSchedule = 'auto'` requires
`performValidationOnSamplesThroughoutTraining = True`, `channelsValidation`,
and `gtLabelsValidation`. Enable sample validation or use `stable`, `predef`,
`poly`, or `expon` instead. Full-volume validation alone is not enough for the
auto scheduler.

**Predefined schedule error**

`predef` requires `predefinedSchedule`, a list of positive integer epoch
boundaries. Ensure the boundaries are meaningful for `numberOfEpochs`; a
schedule entirely after the stopping target will never lower the rate.

**Optimizer or momentum assertion**

Use optimizer selector `0`, `1`, or `2`; momentum type and normalization flags
must be `0` or `1`; momentum must be in `[0,1]`. Adam and RMSProp parameter
names are exact (`b1Adam`, `b2Adam`, `epsilonAdam`, `rhoRms`, `epsilonRms`).
At least one loss weight among `xentr`, `iou`, and `dsc` must be non-`None`.

## Sampling and augmentation

**Sampling category is empty or no samples reach a batch**

Sampling maps are restricted by ROI and by the segment's valid center margin.
A foreground/per-class category can be absent in a case; it is redistributed
among valid categories. If all maps are empty, inspect ROI, label values, image
shape, segment dimensions, and class count. Increase the image or reduce the
segment size only after confirming the data contract. Ensure the sample budget
is at least one full batch and divisible by the batch size.

For type `0`, proportions and weight maps are ordered foreground then
background. For type `3`, they are ordered class `0`, class `1`, and so on.
Uniform and whole-image types accept one category; type `2` currently follows
the same map construction as uniform despite old comments.

**Labels are out of range**

The model's `numberOfOutputClasses` includes background. Labels must be
contiguous integer ids from `0` through `classes-1`. The input check raises
when a maximum label is too large; fix labels or the model config rather than
disabling the check.

**Affine augmentation gives shape, mask, or interpolation problems**

Use interpolation order `0` for labels and ROI masks. Keep affine probability
at `0` while diagnosing. For sample `rotate90`, all requested plane axes must
have equal dimensions; set a plane entry to `None` to disable it. Histogram
`shift` and `scale` each need `mu` and `std`, or should be `None`.

**Parallel sampler hangs, times out, or exhausts RAM**

Set `num_processes_sampling = -1` for main-thread sampling, then `0` for the
single overlap thread. Reduce `numOfCasesLoadedPerSubepoch`, the segment
budget, and augmentation. Only increase positive worker count after sequential
sampling succeeds. A worker failure may be reported at the next `.get()` and
can look like a training failure; read the sampler traceback in the log.

## Checkpoints and restoring

**Checkpoint not found**

Pass the prefix ending exactly with `.model.ckpt`. Do not pass `.index` or
`.data-00000-of-00001`. Check that both the `.index` and at least one `.data-*`
companion exist, and that the path points into the intended session. The
checker lists valid prefixes without loading TensorFlow.

**Restore reports missing variables, shape mismatch, or DataLossError**

Use the same model architecture, input channel count, output class count, and
compatible pathway shapes used to create the checkpoint. A different model
config cannot be resumed by simply changing `-model`. For a deliberate
architecture migration, a custom variable mapping is required and is outside
this skill.

**Resume immediately exits without epochs**

The trainer stores `num_epochs_trained`. A normal resume stops when that value
reaches the current `numberOfEpochs`; check the log for the restored count and
choose a higher target if more training is intended. Do not use `-resetopt` just
to force progress unless resetting the optimizer is intentional.

**Fine-tuning behaves like the old run**

Use `-resetopt` with the pretrained checkpoint. It restores net weights but
reinitializes optimizer accumulators, momentum, learning rate/schedule state,
and epoch count. Confirm the log's optimizer and schedule values are those of
the fine-tune config. Without reset, the old trainer state is intentionally
restored.

**`-resetopt` unexpectedly changes weights**

The code uses a network-only saver to restore `net/*` and initializes only
trainer variables. If weights changed, inspect whether the model architecture
or checkpoint prefix was wrong, or whether a new run omitted `-load`.

## Outputs, metrics, and plotting

**Expected output folders are missing**

The output root is `folderForOutput`, not necessarily the caller's current
folder. The training session creates `logs`, `saved_models/<session>`,
`predictions/<session>/predictions`, `predictions/<session>/features`, and
`tensorboard/<session>`. Use the checker with the same output root and session.
A folder can exist without files when the corresponding validation or logging
feature was disabled.

**No validation predictions**

Full-volume validation must be enabled, its interval must be positive, and
prediction names must be supplied when output is requested. Sample validation
alone does not create whole-volume NIFTI predictions. Full-volume validation
runs only at the configured epoch interval and can be slow.

**TensorBoard is empty**

Set `tensorboard_log=True` before starting the session. Events are written
under separate `train` and `val` subdirectories only when the corresponding
logger is used. Sample metrics are emitted at subepoch steps; full-volume
metrics appear only after whole-volume validation. An old event directory can
make a new run look populated, so use a unique session/output root.

**Progress plotter cannot parse a log or raises on a short run**

Pass a readable text log, not a TensorBoard event file. The parser expects
DeepMedic metric sentences; a log that stopped before the first epoch may have
nothing to plot. Use basic mode first, then detailed mode with valid class ids.
`--classes` is only for `--detailed`. Set `--moving-average 1` for short logs,
and use `--no-show` on headless hosts. Full-volume Dice is validation-only and
may remain at its initial value when full inference never ran.

**Plotting from another working directory fails**

Use the bundled script by its explicit path and pass absolute or otherwise
valid log paths. Set `--output-dir` when saving. The adapted script does not
assume its own directory is the current directory and does not write unless
`--save-figure` is supplied.

## Known code/documentation limits

- Older config comments call type `2` “not implemented”, but current
  `SamplingType` constructs a whole-volume/ROI map through the same branch as
  uniform sampling. Treat it as a one-category whole-image map, not as a
  promise of a distinct sampler.
- The README's historical examples and dependency versions do not fully match
  the verified runtime. Trust the current source signatures and the verified
  runtime facts in the parent skill.
- `expon` remains accepted by the current trainer but is legacy and its
  momentum interpolation is less intuitive than the other schedules. Inspect
  logged LR/momentum values before using it for a long run.
- A successful CLI parse or graph build is not a successful training result;
  data loading, sampling, device allocation, and checkpoint writes happen
  later.
