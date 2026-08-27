---
name: "clustering"
description: "Guides PyPOTS clustering workflows with CRLI and VaDER, including
  cluster inputs, latent outputs, validation metrics, and checkpoint caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# PyPOTS Clustering

Use this sub-skill when the user wants unsupervised cluster assignments for
partially-observed time-series samples.

## Natural Triggers

- "cluster time series with PyPOTS"
- "use CRLI or VaDER"
- "get `predict()[\"clustering\"]`"
- "return latent variables from clustering"
- "compute clustering validation metrics"
- "why did VaDER hit a singular matrix?"

## First References

- Read [`../../references/data-formats.md#clustering`](../../references/data-formats.md#clustering) for `X` and optional `y`.
- Read [`../../references/api-reference.md`](../../references/api-reference.md) for `cluster()` and result keys.
- Read [`../../references/model-overview.md#clustering`](../../references/model-overview.md#clustering) for model selection.
- Read [`../../references/troubleshooting.md`](../../references/troubleshooting.md) for HDF5, checkpoint, and metric
  failures.
- Use [`../cli/`](../cli/SKILL.md) for `pypots-cli train`, `predict`, `evaluate`, `benchmark`, or
  `recommend` configs.

## Scope

This route covers:

- `CRLI` clustering.
- `VaDER` clustering.
- Training with unlabeled `X` plus optional validation labels.
- Cluster extraction through `predict()["clustering"]` or `cluster()`.
- Latent-variable extraction with `return_latent_vars=True`.
- External and internal validation metrics.

Route elsewhere:

- Supervised class labels -> [`../classification/`](../classification/SKILL.md).
- Embeddings without cluster assignment -> [`../representation/`](../representation/SKILL.md).
- Anomaly labels -> [`../anomaly-detection/`](../anomaly-detection/SKILL.md).
- Data conversion and benchmark datasets -> [`../cli/`](../cli/SKILL.md) plus
  [`../../references/data-formats.md`](../../references/data-formats.md).

## Core Workflow

1. Prepare `train_set = {"X": train_X}` with shape
   `[n_samples, n_steps, n_features]`.
2. Choose `n_clusters`; if labels exist, use them only for validation, not as
   supervised training targets.
3. Instantiate the model:
   - `CRLI` needs `n_generator_layers`, `rnn_hidden_size`, and `rnn_cell_type`.
   - `VaDER` needs `rnn_hidden_size`, `d_mu_stddev`, and often
     `pretrain_epochs`.
4. Train with `fit(train_set, val_set)`.
5. Predict:

   ```python
   results = model.predict({"X": test_X}, return_latent_vars=True)
   clusters = results["clustering"]
   latents = results.get("latent_vars")
   ```

6. Evaluate against known labels with
   `calc_external_cluster_validation_metrics()`. Use internal metrics only when
   you pass the right latent representation or feature matrix.

## Minimal Example Shape

```python
from pypots.clustering import CRLI

model = CRLI(
    n_steps=n_steps,
    n_features=n_features,
    n_clusters=n_clusters,
    n_generator_layers=1,
    rnn_hidden_size=32,
    rnn_cell_type="GRU",
    epochs=1,
    device="cpu",
)
model.fit({"X": train_X}, {"X": val_X})
clusters = model.cluster({"X": test_X})
```

## Common Decision Points

- Use `CRLI` when you need explicit latent variables for downstream inspection.
- Use `VaDER` when its variational/deep-clustering assumptions fit the task,
  but be prepared to retrain if Gaussian-mixture internals hit singular-matrix
  issues.
- For fast checks, reduce `epochs` and `pretrain_epochs`; avoid interpreting
  metrics from tiny fixtures as benchmark quality.
- `CRLI` uses generator/discriminator optimizers (`G_optimizer`, `D_optimizer`)
  rather than one generic optimizer.
- If class labels are present, keep them out of training data unless the chosen
  API explicitly asks for validation labels.

## Validation Signals

A successful clustering workflow returns one cluster id per test sample. Native
style checks log external metrics such as Rand index, adjusted Rand index, NMI,
and cluster purity, and may log internal metrics from latent variables.
