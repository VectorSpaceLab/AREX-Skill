# DGL-Go Troubleshooting

## `dgl` Command Missing or Wrong Command Tree

Symptoms:

- Shell says `dgl: command not found`.
- `dgl --help` does not list `configure`, `recipe`, `train`, `export`, `configure-apply`, and `apply`.
- Core `import dgl` works but DGL-Go commands do not.

Fixes:

- Install `dglgo` in the active environment when CLI workflows are required.
- Ensure DGL itself is at least version 0.8 for DGL-Go compatibility.
- Expect heavy optional dependencies from DGL-Go packaging: OGB, RDKit, scikit-learn, pydantic, Typer, YAML packages, autopep8, and isort.
- If a task only needs graph APIs, route away from this sub-skill and use core DGL guidance instead.

## Invalid Pipeline Name

Symptoms:

- `KeyError` for `pipeline_name` during `dgl train` or `dgl export`.
- `dgl configure PIPELINE --help` rejects a pipeline.

Fixes:

- For training configs, use `nodepred`, `nodepred-ns`, `linkpred`, or `graphpred`.
- For apply configs, use `nodepred`, `nodepred-ns`, or `graphpred`; source evidence did not register link prediction apply.
- Run the bundled linter to catch spelling errors before DGL-Go imports the training stack.

## Missing or Malformed Config

Symptoms:

- `dgl train --cfg CFG.yaml` fails opening the file.
- YAML loads as empty, a list, or a scalar.
- Required sections such as `data`, `model`, or `general_pipeline` are missing.

Fixes:

- Generate a fresh config with `dgl configure ... --cfg CFG.yaml` or copy a known recipe with `dgl recipe get ...`.
- Preserve required top-level keys: `pipeline_name`, `pipeline_mode`, `device`, `data`, and `general_pipeline`.
- Use `model` for `nodepred`, `nodepred-ns`, and `graphpred`; use `node_model`, `edge_model`, and `neg_sampler` for `linkpred`.

## Dataset Downloads and Optional Dataset Packages

Symptoms:

- Training stalls or fails while downloading Cora, PubMed, OGB, or molecule data.
- OGB import errors occur for `ogbn-*`, `ogbl-*`, or `ogbg-*` recipes.
- RDKit import errors occur for molecule graph prediction recipes.

Fixes:

- Treat full training as optional unless dataset download and optional dependencies are explicitly acceptable.
- Use `dgl export` and linting for safe validation in constrained environments.
- Switch to a small builtin dataset such as Cora for fast smoke checks where available.
- Change recipe `device` from `cuda` to `cpu` only if the dataset and dependency stack are otherwise available.

## Custom CSV `data_path` Problems

Symptoms:

- Config has `data.name: csv` but no `data.data_path`.
- DGL CSV loader cannot find metadata, node CSVs, or edge CSVs.
- Random split generation fails because `split_ratio` is malformed.

Fixes:

- Set `data.data_path` to the directory containing CSV graph files and metadata.
- Use `split_ratio` as three numeric values that sum to about 1.0 when masks/splits are absent.
- For detailed CSV file schemas and metadata semantics, route to `datasets-and-io`.

## Checkpoint Mismatch in Apply

Symptoms:

- `dgl configure-apply` cannot load `--cpt`.
- `dgl apply` fails with missing model keys or unexpected architecture.
- Apply dataset features do not match the training model.

Fixes:

- Use checkpoints saved by DGL-Go under `general_pipeline.save_path` as `run_i.pth`.
- Keep apply `pipeline_name` consistent with the training pipeline family.
- Confirm the target dataset has compatible feature dimensions and label/output expectations.
- Export the apply script before execution when adapting to new data.

## Link Prediction Config Pitfalls

Symptoms:

- Link prediction export fails after adding `data.split_ratio`.
- Config has `model` instead of `node_model` and `edge_model`.

Fixes:

- If `data.split_ratio` is present, also set `data.neg_ratio`.
- Use `node_model`, `edge_model`, and `neg_sampler` for `linkpred`; do not use the single `model` section.
- Do not assume link prediction has `configure-apply` support unless the installed CLI explicitly lists it.

## Torch, CUDA, and Device Failures

Symptoms:

- Recipe says `device: cuda` or `cuda:0`, but torch reports no CUDA device.
- Checkpoints saved on one device fail to load or apply on another.

Fixes:

- Edit `device: cpu` for CPU-only runs and keep expectations small.
- Verify torch, DGL backend, and CUDA compatibility before long training.
- Use the linter to flag unusual device strings, but rely on runtime checks for actual hardware availability.
