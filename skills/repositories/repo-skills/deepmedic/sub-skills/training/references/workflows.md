# Training workflows

These workflows use the installed `deepMedicRun` entry point and explicit
configuration/checkpoint paths. They do not depend on a particular checkout
layout. Keep the model config and training config under a stable project data
location so that their relative file-list paths remain valid.

## 1. Preflight and tiny smoke

Before allocating a long run:

1. Confirm the model config's input channel count matches the number of
   `channelsTraining` entries and its output class count matches label ids.
2. Run `deepMedicRun -h` and confirm the environment can import DeepMedic and
   TensorFlow. A help check does not load NIFTI data or build the model graph.
3. Use a tiny model and tiny train config with one case, one epoch, one
   subepoch, a segment budget divisible by a small batch size, and
   `num_processes_sampling = -1` or `0`.
4. Start on `-dev cpu` to separate configuration/data failures from CUDA
   failures. Use a dedicated output directory; DeepMedic creates directories
   and writes logs, checkpoints, predictions, and TensorBoard events.
5. Inspect output with the read-only checker and confirm the log includes
   initialization, at least one training subepoch, an epoch save, and normal
   completion. Only then increase segment count, cases, validation, or
   augmentation.

A smoke invocation is:

```text
deepMedicRun -model MODEL_CFG -train TINY_TRAIN_CFG -dev cpu
```

Do not use a production model with a production sample budget merely to test
that the CLI starts. A graph can build successfully while the first sample
load later fails due to list length, NIFTI shape, class, or memory errors.

## 2. CPU versus GPU selection

Use `-dev cpu` for tiny configurations and diagnosis. It clears CUDA visibility
before TensorFlow initializes and binds the model graph to CPU 0.

Use `-dev cuda` when the process should see all available CUDA devices. The
front end leaves device selection to TensorFlow. Use `-dev cudaN` when a
particular host GPU is required; the front end sets visibility to host device
`N` and then addresses the remaining visible device as GPU 0.

A GPU run should be checked in two places:

- the DeepMedic log's TensorFlow device listing and subsequent graph/session
  messages; and
- an external accelerator monitor showing the process on the intended host
  GPU.

If `cuda`/`cudaN` errors during initialization or falls back to CPU, stop and
resolve TensorFlow/CUDA/cuDNN compatibility. Do not assume a requested flag
made the run accelerated. The verified reference environment uses TensorFlow
2.6.2 with a CUDA 11.2 build and A100 hardware, but this is not a universal
compatibility prescription.

## 3. Production-oriented training

A production config normally sets:

- a unique `sessionName` and a new `folderForOutput`;
- all training modality lists and `gtLabelsTraining`, with an optional ROI;
- enough `numberOfEpochs` and `numberOfSubepochs` for the planned study;
- a segment budget divisible by `batchsize_train`;
- `num_processes_sampling = 0` initially, then a measured positive value if
  file I/O and RAM permit;
- a deliberate sampling selector and class proportions;
- a schedule chosen from observed behavior rather than copied blindly;
- `tensorboard_log = True` only when the event storage is acceptable; and
- validation settings that do not make full-volume inference dominate every
  epoch.

Use stable LR for a baseline when the correct duration is uncertain, or use a
predefined schedule whose epoch boundaries fit the total epoch count. `auto`
requires sample validation and should not be selected in a config that disables
it. Full-volume validation is useful for segmentation quality but is much more
expensive than sample metrics; set
`numberOfEpochsBetweenFullInferenceOnValImages` accordingly.

At each epoch DeepMedic saves the complete graph state. Keep enough disk space
for many checkpoint sets, event files, text logs, and optional validation
NIFTIs. The output checker can summarize candidates without opening TensorFlow
or mutating the directory.

## 4. Resume an interrupted run

Choose a checkpoint set produced at the end of a completed epoch. Pass the
prefix ending exactly in `.model.ckpt`:

```text
deepMedicRun -model MODEL_CFG -train TRAIN_CFG \
  -load OUTPUT/saved_models/SESSION/MODEL.SESSION.TIMESTAMP.model.ckpt \
  -dev cudaN
```

Do not pass `.index` or `.data-00000-of-00001`. Use the same architecture config
and compatible class/channel dimensions. Without `-resetopt`, DeepMedic
restores both `net/*` weights and `trainer/*` variables, including the saved
epoch counter, optimizer state, and schedule state. It then continues until
`numberOfEpochs` in the current train config. If the saved epoch counter is
already at or above the target, no additional training epoch is performed.

If a job stopped in the middle of an epoch, the last checkpoint is the prior
completed epoch. Sampling and metric output from the interrupted epoch are not
an atomic resumable transaction; restarting from the last saved epoch is the
safe expectation.

## 5. Fine-tune or reset the optimizer

For a pretrained network on a new dataset or schedule:

```text
deepMedicRun -model MODEL_CFG -train FINETUNE_CFG \
  -load PRETRAINED_PREFIX.model.ckpt -resetopt -dev cudaN
```

`-resetopt` is not a weight reset. The session restores the network saver
(`net/*`) from the checkpoint, initializes trainer variables (`trainer/*`),
and starts the new epoch counter, optimizer accumulators, learning-rate state,
and momentum state from `FINETUNE_CFG`. This is the intended fine-tuning
operation when the old optimizer trajectory should not be continued.

Do not add `-resetopt` to an ordinary resume unless you intentionally want to
restart optimization. Conversely, omitting it during fine-tuning carries over
momentum/Adam/RMSProp state and the old training epoch/schedule, which can make
the new config appear ineffective.

Layer freezing is configured in the train config and is applied when the
trainer chooses trainable parameters. Verify the log's printed freeze lists
and optimizer settings before committing a long fine-tune.

## 6. Metrics, TensorBoard, and plotting

The text log is the authoritative human-readable record. Sample metrics are
reported at every subepoch and epoch; full-volume Dice appears only when whole
validation inference runs. Class-0 reports merged foreground, while other
classes use one-vs-all calculations.

When `tensorboard_log=True`, point TensorBoard at the session directory (the
parent containing `train` and `val` event subdirectories). Do not parse event
files as text. The text log and bundled plotter are safer for automated checks.

For a headless explicit plot:

```text
python sub-skills/training/scripts/plot_training_progress.py LOG.txt \
  --detailed --classes 1 --moving-average 20 \
  --save-figure --output-dir PLOTS --no-show
```

For a basic overall-accuracy plot:

```text
python sub-skills/training/scripts/plot_training_progress.py LOG.txt --save-figure --output-dir PLOTS --no-show
```

Multiple logs may be supplied. In detailed mode, one class applies to every
log; one class per log can be supplied when the counts match. `--classes` is
invalid in basic mode. The parser carries forward `N/A` values as the original
utility, uses a moving average for sample curves only, and leaves full-volume
Dice unsmoothed. `--save-figure` writes `trainingProgress.pdf` under the
explicit output directory; without `--save-figure`, no figure is written.

## 7. Read-only output inspection

After a run, execute:

```text
python sub-skills/training/scripts/check_training_outputs.py OUTPUT --session SESSION
```

The checker reports expected logs, model/prediction/feature/TensorBoard
folders, checkpoint prefixes with `.index` and `.data-*` companions, and
whether the log contains completion markers. It never creates, deletes, or
rewrites files. Use `--json` for machine-readable output and `--help` for all
options.

The standard training tree is:

```text
OUTPUT/
  logs/SESSION.txt
  saved_models/SESSION/<model>.<session>.<timestamp>.model.ckpt.{index,data-*}
  predictions/SESSION/predictions/       # full validation output when enabled
  predictions/SESSION/features/          # feature maps when enabled
  tensorboard/SESSION/train/             # if tensorboard_log=True
  tensorboard/SESSION/val/               # if validation logging is enabled
```

The exact model prefix comes from the model config's `modelName` and the train
session name. Initial, per-epoch, and final checkpoint prefixes differ by
suffixes such as `.initial.`, timestamps, and `.final.`. A loaded run does not
write a new initial checkpoint. Prediction folders may exist even when no
prediction file has yet been emitted; use the log and checker together.
