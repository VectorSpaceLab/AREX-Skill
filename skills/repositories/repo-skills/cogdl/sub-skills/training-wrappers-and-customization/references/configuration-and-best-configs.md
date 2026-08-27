# Configuration and Best-Config Reference

## Purpose

Read this when the user wants `use_best_config`, `set_best_config`, or a
reusable training configuration template.

## How the best-config path works

`set_best_config(args)` checks `BEST_CONFIGS[args.model]` and applies:

1. the model's `general` defaults
2. any dataset-specific overrides when the dataset key exists

The CLI/API flag `use_best_config=True` simply asks the experiment path to
apply that helper before the trainer starts.

## Representative observed profiles

| Model | Observed general override | Example dataset-specific overrides |
| --- | --- | --- |
| `gat` | `lr=0.005`, `epochs=1000` | `citeseer`, `pubmed`, and `ppi-large` define dataset-specific changes |
| `gcn` | default general profile | `ppi-large` and `flickr` define tuned values |
| `gcnii` | `epochs=1000`, `dropout=0.5`, `wd1=0.001`, `wd2=5e-4` | `cora`, `citeseer`, `pubmed`, `reddit`, and `flickr` each override multiple fields |
| `grand` | `epochs=1000` | `cora`, `citeseer`, and `pubmed` have different `order`, `sample`, `lam`, `tem`, `alpha`, and dropout values |
| `ppnp` | empty general profile | `cora`, `citeseer`, `pubmed`, `reddit`, and `flickr` all customize propagation and dropout fields |
| `grace` | `weight_decay=0`, `epochs=1000`, `patience=20` | `cora`, `citeseer`, and `pubmed` customize learning rates, augmentation, and hidden sizes |

## What to keep explicit in configs

- `epochs`, `lr`, `weight_decay`, and `hidden_size` are common tuning knobs.
- `cpu`, `devices`, and `distributed` must be stated when device behavior
  matters.
- `checkpoint_path`, `save_emb_path`, `load_emb_path`, and `log_path` are
  file-write surfaces and should be set to writable locations.
- `resume_training` only makes sense when the checkpoint matches the current
  model shape and compatible settings.
- `actnn`, `fp16`, `cpu_inference`, and `rp_ratio` are advanced execution
  flags and should be left at defaults unless the task really needs them.

## Template reasoning

If a user asks for a reusable config, separate the answer into:

- model and data identity
- wrapper pair
- trainer/optimizer fields
- output paths
- device/distributed fields
- optional runtime flags

That separation makes the config easier to review before any run starts.
