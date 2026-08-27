# Evaluation and metrics

## What the test path does

`tools/test.py` loads the selected config, marks the test dataset as
`test_mode=True`, builds its dataloader, builds the model, and loads the
checkpoint with MMCV `load_checkpoint(..., map_location='cpu')`. It then runs
single-GPU or custom multi-GPU inference. Distributed inference collects result
parts through GPU communication or rank-local pickle files. This requires CUDA
for the distributed path and real SemanticKITTI data; loading the Python
metric class is not an evaluation result.

Use one or more operations explicitly:

```bash
python tools/test.py <config> <checkpoint>.pth --eval <metric>
python tools/test.py <config> <checkpoint>.pth --show-dir <result-dir>
python tools/test.py <config> <checkpoint>.pth --format-only \
  --eval-options <key>=<value>
```

The parser rejects a command with none of `--out`, `--eval`, `--format-only`,
`--show`, or `--show-dir`, rejects `--eval` with `--format-only`, and requires a
`.pkl`/`.pickle` suffix for `--out`. In the inspected implementation, the
`--out` branch prints a message and then executes `assert False` instead of
dumping outputs; treat `--out` as a known implementation limitation, not a
verified result-saving route. Do not claim that `--out` produced a file unless
the implementation has been corrected and tested.

The distributed shell wrapper appends `--eval bbox` regardless of the dataset.
For SSC evaluation, prefer a direct command with the desired explicit metric
(or inspect the installed dataset evaluator) rather than assuming the wrapper's
generic `bbox` default is meaningful.

## SSC evaluator contract

Both inspected SemanticKITTI dataset classes implement `evaluate(results, ...)`
and return a dictionary. Each result is expected to contain:

- `y_pred`: predicted semantic voxel labels, compatible in shape with `y_true`;
- `y_true`: ground-truth semantic voxel labels, with `255` treated as ignored.

The evaluator feeds every result to `SSCMetrics.add_batch(y_pred, y_true)` and
then returns keys under the `ssc_SemanticKITTI/` prefix:

- one `SemIoU_<class>` value per dataset class;
- `ssc_SemanticKITTI/mIoU`: mean semantic IoU excluding class index 0 in
  `iou_ssc_mean`;
- `ssc_SemanticKITTI/IoU`: binary completion IoU (all labels > 0 are occupied);
- `ssc_SemanticKITTI/Precision` and `ssc_SemanticKITTI/Recall`: binary
  completion precision/recall.

`SSCMetrics` uses the following behavior:

- `255` is ignored for semantic/completion accounting;
- completion maps every nonzero class to occupied class 1;
- semantic class counts are accumulated across batches;
- `iou_ssc` is per-class `tp / (tp + fp + fn + 1e-5)`;
- the reported semantic mean is `np.mean(iou_ssc[1:])`;
- completion precision/recall/IoU are computed from aggregate occupied
  true-positive, false-positive and false-negative counts.

The evaluator resets its metric accumulator after producing the dictionary.
Metrics are therefore tied to the exact result list and ground-truth labels for
that invocation; do not combine printed values from separate runs without
preserving the sample set and config.

## Training-time validation

The custom training API registers an evaluation hook when `tools/train.py` is
run without `--no-validate`. The hook uses the validation dataset and the
custom multi-GPU test collector. The `evaluation.interval` in the configs is
one epoch. The custom hook accepts `greater_keys=['mIoU']` for best-checkpoint
logic when configured, and uses a work-directory `.eval_hook` temporary path by
default. The standard S/T configs set `evaluation=dict(interval=1)` and
`checkpoint_config=None`; QPN sets an evaluation pipeline and checkpoints at
interval one. Validation is expensive and still needs complete stage-specific
data.

`--no-validate` only disables training-time validation; it does not make the
training path CPU-safe or remove the need for data and CUDA.

## Result directories and files

Distinguish these output classes:

- `<work-dir>/`: dumped config, timestamped logs, runner/checkpoint artifacts,
  and possible validation temporary state;
- `<show-dir>/`: visualization output requested by `--show-dir`;
- `<tmpdir>/`: operator-selected distributed collection workspace; when omitted,
  the custom collector creates rank files below `.dist_test` and removes its
  temporary directory after rank-0 collection;
- evaluator prefixes: `tools/test.py` passes a generated `jsonfile_prefix` below
  a `test/<config-stem>/...` namespace for dataset formatting/evaluation kwargs.

These locations can collide with stale or concurrent runs. Choose unique,
operator-approved paths and inspect before reuse. The skill's preflight only
reports existence and potential collisions; it never creates or cleans paths.

The model head also has a `save_pred` helper that writes SemanticKITTI-style
labels under a `voxformer/sequences/<sequence>/predictions/` tree when that
code path is used. This is separate from the `tools/test.py --show-dir` and
`--out` paths; do not assume one output implies the other.

## What remains unverified

- No full train/test run was performed during skill creation.
- No real SemanticKITTI labels, query files, predictions, result directory, or
  checkpoint was available for a final evaluator call.
- No final IoU, mIoU, precision, or recall values are claimed. README headline
  numbers are reported project references, not reproduction evidence.
- The distributed collector, output formatting, visualization, and evaluator
  behavior were inspected statically; their multi-GPU runtime behavior still
  requires a prepared CUDA environment, compatible legacy dependencies, real
  data, and an explicitly approved run.
- `SSCMetrics` import succeeds in the prepared inspection environment, but this
  does not verify tensor/array shapes, class mapping, sample completeness, or
  numerical correctness on the target dataset.
