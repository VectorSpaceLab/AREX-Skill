# GraphGym Troubleshooting

GraphGym is an optional PyG subsystem and may require extra packages beyond core `torch_geometric`. Start with config validation and dependency checks before running training.

## Missing Optional Dependencies

Common symptoms:

- `Could not define global config object` or `No module named 'yacs'`: install the GraphGym optional dependencies or at least `yacs`.
- Import errors for `pytorch_lightning` or `lightning`: GraphGym training uses Lightning-backed trainer utilities in current PyG.
- Import errors for `google.protobuf` or protobuf-related parsing: install a compatible `protobuf` package.
- General GraphGym optional dependency failures: install PyG with its GraphGym extra when available, for example `pip install "torch-geometric[graphgym]"` in a compatible environment.

The bundled validator reports whether `yaml`, `yacs`, `pytorch_lightning`/`lightning`, and `google.protobuf` are importable. It does not require them to perform static checks except for YAML parsing.

## Invalid Config Keys or Types

GraphGym configs are sectioned. A typo such as `gnn.layer_typ` will not select the intended layer. Use the validator to flag unrecognized top-level sections and common nested-key typos.

Common type issues:

- `train.batch_size`, `optim.max_epoch`, `gnn.layers_mp`, and `gnn.dim_inner` should be positive integers.
- `optim.base_lr`, `gnn.dropout`, and split ratios should be numeric.
- `dataset.split` should be a list of two or three numeric ratios.
- Boolean fields such as `dataset.node_encoder`, `dataset.edge_encoder`, `gnn.batchnorm`, and `train.enable_ckpt` should be booleans, not strings like `"false"`.

GraphGym may post-process some values. For example, classification tasks use cross entropy, regression tasks use MSE, graph tasks are non-transductive, and at least one post-message-passing layer is enforced.

## Registry Name Collisions

Registration helpers raise `KeyError` if a key already exists. This is intentional: silently replacing a layer, loss, activation, or dataset would make experiments unreproducible.

Recovery steps:

1. Print or inspect the relevant registry dictionary before registering.
2. Rename the custom key or remove the duplicate import path.
3. Ensure tests do not register the same key at module import time across repeated test processes.
4. Keep config values aligned with the final key name.

## Run Directory Confusion

GraphGym derives output folders from the configured `out_dir`, config filename, and seed/repeat behavior. Per-seed directories and aggregated directories are both expected. If a metric file is missing, check:

- Was the run interrupted before aggregation?
- Did `--repeat` create multiple seed directories?
- Did `train.enable_ckpt`, `train.ckpt_period`, or result logging settings change write behavior?
- Did `out_dir` point to a different relative directory than expected?
- Was an existing output directory removed because auto-resume was disabled?

Always resolve result paths relative to the process working directory used for the GraphGym run.

## Benchmark-Scale Side Effects

Batch runs can generate many configs, start many jobs, download datasets, and write large result trees. Before running a batch job, confirm:

- The grid file is reviewed and bounded.
- `MAX_JOBS` is appropriate for the machine.
- Dataset downloads and cache writes are allowed.
- `out_dir` points to disposable or intended storage.
- A single small CPU run has already passed.

When uncertain, validate YAML and registry setup only; do not launch training.
