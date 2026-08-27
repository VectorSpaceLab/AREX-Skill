# Fair Graph Workflows

## Dataset Loading

1. Choose NBA or POKEC.
2. Instantiate the dataset with the desired root and sample type.
3. Inspect `features`, `labels`, `sens`, `adj`, and the split indices before training.

## Graphair Training

1. Create a `torch.device`.
2. Build the runner with `run()`.
3. Call `run.run(device, dataset=..., model='Graphair', epochs=..., test_epochs=..., lr=..., weight_decay=...)`.
4. Inspect the printed fairness/accuracy summaries.

## Metric Checks

- Use `accuracy` for simple binary outputs.
- Use `fair_metric` to report parity and equality-gap style numbers on sensitive subgroups.
