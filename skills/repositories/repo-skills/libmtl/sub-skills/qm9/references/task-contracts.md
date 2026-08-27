# QM9 Task Contracts

This file distills the benchmark-specific task dictionary, target handling, and
model wiring for the QM9 workflow.

## Dataset contract

- The benchmark uses the QM9 molecular dataset from `torch_geometric.datasets`.
- The default target list contains 11 regression indices.
- A bundled split artifact, `references/random_split.t`, defines the train,
  validation, and test slices.

## Task dictionary shape

For each target index `t`:

- `metrics=['MAE']`
- `metrics_fn=QM9Metric(std[:, t], scale)`
- `loss_fn=MSELoss()`
- `weight=[0]`

The `scale` value is `1000` for targets `[2, 3, 6, 12, 13, 14, 15]` and `1`
otherwise.

## Model wiring

- Node embedding: `Linear(11, dim)`
- Message passing: `NNConv(dim, dim, nn, aggr='mean')`
- Sequence model: `GRU(dim, dim)`
- Pooling: `Set2Set(dim, processing_steps=3)`
- Decoder: one `nn.Linear(64, 1)` per selected target

## Trainer notes

- The benchmark overrides the scheduler to `reduce` with `mode='max'`,
  `factor=0.7`, `patience=5`, and `min_lr=1e-5`.
- The workflow uses the shared LibMTL trainer, so CUDA still applies.
