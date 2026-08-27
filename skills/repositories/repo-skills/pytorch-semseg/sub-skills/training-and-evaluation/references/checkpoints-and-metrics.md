# Checkpoints, Logs, Metrics, and State Dicts

Use this reference to interpret outputs from `train.py` and `validate.py` and to
adapt checkpoints between training and validation safely.

## Training checkpoint format

Training saves a checkpoint dictionary when validation `Mean IoU : \t` improves
or ties the previous best. The file name is built from the model architecture and
dataset id:

```text
<arch>_<dataset>_best_model.pkl
```

It is written inside the current TensorBoard run directory. Expected fields:

| Field | Meaning | Notes |
| --- | --- | --- |
| `epoch` | The one-based training iteration at save time | Used as `start_iter` when resuming. |
| `model_state` | `model.state_dict()` from the training model | Training wraps the model in `DataParallel`, so keys commonly start with `module.`. |
| `optimizer_state` | Optimizer state dict | Resume expects the same optimizer family and compatible parameter groups. |
| `scheduler_state` | Scheduler state dict | Resume expects a compatible scheduler configuration. |
| `best_iou` | Best mean IoU observed so far | Used for bookkeeping, not for validation loading. |

Resume reads `training.resume` from the config. If the path exists, the script
loads model, optimizer, scheduler, and epoch. If it does not exist, it logs that
no checkpoint was found and starts training from scratch. The path is resolved
from the process working directory, not automatically from the config file's
parent directory.

## Validation checkpoint loading

Validation expects `model_path` to point to a checkpoint dictionary with a
`model_state` field:

```text
torch.load(model_path)["model_state"]
```

The validation model is not wrapped in `DataParallel`. Before loading, validation
passes the saved model state through `convert_state_dict`:

- If the first key starts with `module.`, every key has that prefix removed.
- If keys do not start with `module.`, the state dict is returned unchanged.

This makes normal validation compatible with checkpoints saved by the training
loop's `DataParallel` model. It also handles checkpoints saved from a non-parallel
model. It does not fix architecture mismatches, class-count mismatches, missing
`model_state`, mixed prefix styles, or checkpoints that store a raw state dict
without the expected wrapper dictionary.

## TensorBoard and logger outputs

Training creates a run directory using this pattern:

```text
runs/<config-stem>/<random-run-id>/
```

Inside that run directory it writes:

- A copy of the config used for the run.
- TensorBoardX event files.
- A timestamped logger file.
- Best-checkpoint files named `<arch>_<dataset>_best_model.pkl`.

TensorBoard scalar tags written by training include:

| Tag pattern | Source | Meaning |
| --- | --- | --- |
| `loss/train_loss` | Training loop | Most recent training loss at `print_interval`. |
| `loss/val_loss` | Periodic validation inside training | Average validation loss over the validation loader. |
| `val_metrics/<score-key>` | Periodic validation inside training | Aggregate metrics from `runningScore.get_scores()`. |
| `val_metrics/cls_<class-index>` | Periodic validation inside training | Per-class IoU for numeric class ids. |

The aggregate score keys contain punctuation and tab characters exactly as shown
below, so TensorBoard tags and logs may look unusual:

- `Overall Acc: \t`
- `Mean Acc : \t`
- `FreqW Acc : \t`
- `Mean IoU : \t`

## Validation console metrics

After processing the validation loader, validation prints each aggregate score
key and value, followed by one line per class index:

```text
Overall Acc: \t <value>
Mean Acc : \t <value>
FreqW Acc : \t <value>
Mean IoU : \t <value>
0 <class-0-iou>
1 <class-1-iou>
...
```

`runningScore` maintains an `n_classes x n_classes` confusion matrix. Its metrics
are computed as:

| Metric | Interpretation |
| --- | --- |
| Overall Acc | Total correct pixels divided by total valid pixels. |
| Mean Acc | Mean of per-class pixel accuracies, ignoring classes that become NaN. |
| FreqW Acc | Frequency-weighted IoU over classes present in the ground truth. |
| Mean IoU | Mean intersection-over-union over classes, ignoring NaN classes. |
| Class IoU | IoU for each numeric class id. |

For class names and dataset-specific label meanings, route to `data-and-configs`.
This sub-skill only interprets the numeric metric output.

## Ignore labels and NaNs

Metric updates mask out labels outside `[0, n_classes)`. The training losses use
`ignore_index=250`, so labels with value `250` are ignored by loss and also fall
outside normal class ranges for common segmentation datasets. NaNs can still
appear when:

- A class has no ground-truth pixels in the validation subset.
- A class has no predictions and no ground-truth pixels, making IoU undefined.
- All labels in a small smoke dataset are ignored or invalid.
- The validation loader is empty or points at the wrong split.

For real evaluation, report both aggregate metrics and the validation data/split
used. Do not compare metrics across configs unless image size, splits,
preprocessing, checkpoint architecture, and flip mode are consistent.

## Flip averaging and fps

With `--eval_flip`, validation runs the model on original images and horizontally
flipped images, reverses the flipped outputs, averages the two output arrays, and
then computes `argmax`. This can improve robustness but roughly doubles inference
work.

With `--measure_time`, validation prints per-batch fps as batch size divided by
elapsed wall time for that validation iteration. Treat this as a rough workflow
signal rather than a rigorous benchmark because it includes data/device movement,
can include flip averaging, has no warm-up protocol, and does not explicitly
synchronize CUDA timing.

## Checkpoint sanity checklist

Before asking a future agent to validate a checkpoint, verify these facts without
starting a dataset run:

- The checkpoint file exists and is trusted local data.
- The config model architecture matches the checkpoint architecture.
- The config dataset implies the same `n_classes` used for training.
- The checkpoint dictionary contains `model_state` for validation.
- If resuming training, the checkpoint also contains optimizer and scheduler states.
- If changing optimizer/scheduler settings after a resume, expect state loading to fail or behave unexpectedly.
- If state dict keys have `module.` prefixes, validation's `convert_state_dict` should strip them; if the prefix pattern is mixed, create a clean adapted checkpoint first.
