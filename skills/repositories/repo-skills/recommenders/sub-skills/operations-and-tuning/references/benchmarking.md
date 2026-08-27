# Benchmarking Reference

## Purpose

Use this to interpret or plan Recommenders benchmark-style comparisons without launching expensive notebooks by default.

## Benchmark loop shape

A typical Recommenders benchmark loop has these stages:

1. Load a dataset such as MovieLens.
2. Split into train/test with a documented ratio and seed.
3. Train each selected algorithm with fixed hyperparameters.
4. Score held-out pairs or recommend top-k items.
5. Compute rating/ranking metrics such as RMSE, MAE, MAP, nDCG, precision, and recall.
6. Record runtime, hardware, backend, and data size.

The repository's benchmark evidence includes CPU, Spark, and GPU model families. Do not compare metrics across backends unless hardware, dataset size, and hyperparameters are reported.

## Safe benchmark planning

For a user's benchmark request, first decide:

- Which models are in scope.
- Whether the run is a smoke test, functional comparison, or performance benchmark.
- Dataset size and whether downloads are allowed.
- Backends: base CPU, Spark, GPU, experimental packages.
- Maximum runtime/cost.
- Metrics and `k`/threshold settings.

## Smoke-test alternative

When full benchmarks are not approved, run or propose small checks:

- Data-preparation validator on a tiny fixture.
- Modeling SAR/TF-IDF tiny smoke scripts.
- Evaluation metric tiny smoke script.
- A bounded parameter grid from `generate_param_grid`.

These prove workflow wiring, not benchmark quality.

## Reporting benchmark results

Use this template:

```text
Dataset: <name/version/size/cache>
Split: <method/ratio/seed/filtering>
Models: <families and dependencies>
Backend: <CPU/GPU/Spark details>
Metrics: <rating/ranking/beyond-accuracy settings>
Runtime: <per stage>
Skipped: <models/backends and reasons>
Limitations: <sample size, optional dependencies, hardware>
```

## Common benchmark pitfalls

- Running GPU models without confirming TensorFlow/PyTorch CUDA availability.
- Installing `[all]` or `[experimental]` just for a small comparison.
- Comparing a full Spark run to a tiny CPU smoke fixture.
- Reporting top-k metrics without remove-seen behavior.
- Treating downloaded public dataset versions as interchangeable.
- Ignoring cold-start users/items filtered during splitting.
