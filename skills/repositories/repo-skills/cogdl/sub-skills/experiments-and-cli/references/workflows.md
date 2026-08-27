# Workflows

## 1. No-network plan: compare GCN and GAT on Cora with two seeds

Use this when the user wants a safe plan rather than an immediate training run.

### API shape

```python
from cogdl import experiment

experiment(
    dataset="cora",
    model=["gcn", "gat"],
    seed=[0, 1],
    cpu=True,
    epochs=200,
)
```

### CLI shape

```bash
python scripts/train.py --dataset cora --model gcn gat --seed 0 1 --cpu --epochs 200
```

### What to tell the user

- This compares two models across two seeds, so the result table will aggregate four runs.
- `--cpu` makes the plan safer when GPU availability is unknown.
- `cora` is a built-in dataset and may download on first use; if the cache is missing, the run is no longer no-network.
- `gcn` and `gat` share the default node-classification wrapper pair, so they can be compared in one call.

### Expected output shape

A result dictionary keyed by `('cora', 'gcn')` and `('cora', 'gat')`, with a printed table of `test_acc` and `val_acc` means/stdevs.

## 2. Save and resume a checkpoint

Use this when the user wants the command-line or API form for a resumable run.

### API

```python
experiment(
    dataset="cora",
    model="gcn",
    checkpoint_path="gcn_cora.pt",
    resume_training=True,
)
```

### CLI

```bash
python scripts/train.py --dataset cora --model gcn --checkpoint-path gcn_cora.pt --resume-training
```

### Notes

- The checkpoint path is a write target; choose a location the user controls.
- `resume_training=True` only makes sense when the checkpoint matches the same model shape and compatible training settings.

## 3. Save or reload embeddings

Use this when the requested model is an embedding model such as `prone`.

### Save

```python
experiment(
    dataset="blogcatalog",
    model="prone",
    save_emb_path="prone_blog.npy",
)
```

### Evaluate saved embeddings

```python
experiment(
    dataset="blogcatalog",
    model="prone",
    load_emb_path="prone_blog.npy",
    num_shuffle=5,
    training_percents=[0.1, 0.5, 0.9],
)
```

### Notes

- `save_emb_path` and `load_emb_path` are file writes/reads.
- Embedding evaluation may use node-classification-style downstream scoring instead of model training.

## 4. Use `use_best_config`

Use this when the user wants the known CogDL default tuning profile.

```python
experiment(dataset="citeseer", model="gat", use_best_config=True)
```

Observed best-config behavior:
- `gat` has a general profile with `lr=0.005` and `epochs=1000`.
- dataset-specific overrides exist for datasets such as `citeseer`, `pubmed`, and `ppi-large`.
- `gcn` also has dataset-specific values such as `flickr` and `ppi-large`.

## 5. Optuna search-space pattern

Use this when the user wants automatic hyperparameter search.

```python
def search_space(trial):
    return {
        "lr": trial.suggest_categorical("lr", [1e-3, 5e-3, 1e-2]),
        "hidden_size": trial.suggest_categorical("hidden_size", [32, 64, 128]),
        "dropout": trial.suggest_uniform("dropout", 0.5, 0.8),
    }

experiment(
    dataset="cora",
    model="gcn",
    seed=[1, 2],
    search_space=search_space,
    n_trials=3,
)
```

### Notes

- `search_space(trial)` must return a dict of arguments to merge into the namespace.
- If the user does not specify a validation metric, CogDL searches for a key containing `Val` or `val`.
- Optuna is an optional dependency surface; compatibility issues can arise with very new matplotlib releases.

## 6. Result-table interpretation

- Each model/dataset combination is treated as a variant key.
- Multiple seeds are averaged per metric.
- The CLI table prints `mean±std` values.
- A `KeyError` during AutoML usually means the run did not expose a validation metric field the search loop could recognize.
