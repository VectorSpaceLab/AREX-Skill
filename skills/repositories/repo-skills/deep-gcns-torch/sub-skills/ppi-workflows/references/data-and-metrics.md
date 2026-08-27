# PPI data, metrics, and checkpoints

## Dataset contract

The PPI workflow uses the PyG `PPI` dataset with three split names: `train`,
`val`, and `test`. The standard dataset contains 20 training graphs, 2
validation graphs, and 2 test graphs, with approximately 2,245 nodes and
61,318 directed edges per graph on average. Each node has 50 floating-point
features and 121 binary gene-ontology targets.

A prepared local data root must be supplied with `--data_dir`. A normal PyG
installation may try to fetch and process `ppi.zip` when the root is missing
raw/processed data; that behavior is intentionally outside this skill. Before
an offline run, the caller should verify the split files and dependency stack
without invoking the dataset constructor in a way that can download.

For each graph, the model-facing fields are:

- `x`: floating-point node features, `[N, 50]` by default.
- `edge_index`: graph connectivity, `[2, E]`, consumed by static sparse graph
  convolutions.
- `y`: floating-point multilabel indicators, `[N, 121]` by default.
- `batch`: added by a collating loader for a batch of graphs; it has length
  equal to the concatenated node count. The PPI `DeepGCN.forward` reads it but
  does not use it to build or alter the static graph computation.

`n_classes` is inferred from `test_dataset.num_classes`, so the test split must
be present and must have the same label width as train/validation. A changed
feature width requires `--in_channels` and a correspondingly constructed first
layer; a changed label width requires a new prediction head.

## Model output and loss

The head and every static block preserve one row per node. The final prediction
has shape `[N, C]`, where `C` is the inferred number of classes. The training
criterion is:

```python
torch.nn.BCEWithLogitsLoss()(logits, y)
```

Targets therefore represent independent binary labels, not one multiclass
class index. Do not replace this with cross-entropy or apply sigmoid before the
loss. For scoring, the source thresholds raw logits:

```python
predicted = logits > 0
```

This is equivalent to applying sigmoid and thresholding at 0.5, but retaining
logits is the correct loss path.

## Micro and macro F1

For multilabel predictions, **micro F1** aggregates true positives, false
positives, and false negatives over all node-label decisions before computing
one F1 value:

```text
micro-F1 = 2 * TP / (2 * TP + FP + FN)
```

The source calls `sklearn.metrics.f1_score` with `average="micro"` for both
training and evaluation. It reports this value with labels such as `mF1` and
`m-F1`; those labels do not mean macro F1.

**Macro F1** computes one F1 per label and averages the 121 label scores:

```text
macro-F1 = mean(F1(label_1), ..., F1(label_C))
```

The source does not calculate macro F1. If a downstream request requires it,
compute it as a separately identified evaluation statistic with
`average="macro"` on the same binary target/prediction arrays, and report the
averaging rule and zero-division policy. Do not relabel the source micro score
as macro or compare the two without preserving their aggregation semantics.

The source weights each loader batch's micro F1 by its node count and averages
those batch scores. With `batch_size=1`, this is one score per PPI graph. With
larger batches, it is a node-weighted mean of per-loader-batch micro scores,
which is not necessarily identical to concatenating every split's predictions
and calling micro F1 once. Recompute a global score if exact cross-graph
aggregation is required.

Training logs include loss, train micro F1, validation micro F1, test micro F1,
and best-so-far validation/test values. Best-checkpoint selection compares the
micro-F1 values with `>`; loss is not the selection metric.

## Checkpoint alignment

The logical architecture identity encoded in a source checkpoint basename is:

```text
ppi-{block}-{conv}-{n_blocks}-{n_filters}_{phase}_best.pth
```

where `phase` is normally `val` or `test`. Before loading, align all of the
following:

1. `block`: `res`, `plain`, or `dense`.
2. `conv`: the graph convolution used by the checkpoint.
3. `n_blocks`: the depth used to construct the backbone.
4. `n_filters`: the hidden width; dense blocks make every later width depend on
   this value.
5. `in_channels`: normally 50, which determines the head weight shape.
6. `n_heads`: especially for GAT; use a compatible output width.
7. `act`, `norm`, `bias`, and `dropout` when exact continuation or evaluation
   comparability matters.
8. `n_classes`: inferred from the data and determines the final prediction
   layer shape.

A matching-looking filename is not proof of matching tensors. Missing or
unexpected keys and prediction-head size errors are usually an architecture or
label-width mismatch, not a reason to ignore the error.

The PPI save path stores a payload shaped conceptually as:

```text
{
  epoch,
  state_dict,
  optimizer_state_dict,
  scheduler_state_dict,
}
```

The model state is copied to CPU before saving. The loader also handles a
leading `module.` prefix when moving between DataParallel and non-DataParallel
models. This prefix normalization cannot fix different depth, widths,
convolution choices, or output class counts. A training resume additionally
needs optimizer and scheduler state compatible with the current device and
optimizer configuration; test-only loading needs the model `state_dict`.

## Split and reporting discipline

Use validation micro F1 for model selection when making a fair held-out claim.
The source also tracks test-best and, after training, evaluates both
validation-best and test-best on the test loader. The latter is a test-informed
selection path. Preserve which checkpoint was selected and which split was
scored in any report; do not rely on the source log phrase that calls the first
post-training result a validation-dataset test.
