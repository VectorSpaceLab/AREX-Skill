# DGL Cross-Cutting Troubleshooting

## Import Fails Before Any Task Runs

Symptoms:

- `RuntimeError: Cannot find the files` with `libdgl.so` candidates.
- `FileNotFoundError: Cannot find DGL C++ graphbolt library ... libgraphbolt_pytorch_<version>.so`.
- `ModuleNotFoundError: No module named 'torchdata.datapipes'`.
- Backend import errors after setting `DGLBACKEND`.

Checks:

```bash
python scripts/check_dgl_environment.py
python - <<'PY'
import importlib.metadata as md
for name in ['dgl', 'torch', 'torchdata']:
    try:
        print(name, md.version(name))
    except Exception as exc:
        print(name, type(exc).__name__, exc)
PY
```

Likely causes and recovery:

- Missing `libdgl` means source build outputs are absent or `DGL_LIBRARY_PATH` is wrong. Use a published wheel for normal package usage or complete a source build.
- Missing GraphBolt library for the installed torch version means the DGL wheel and torch ABI are mismatched. Install a compatible DGL wheel or pin torch to a supported version.
- Missing `torchdata.datapipes` means torchdata is too new or incompatible for the installed DGL version. Pin torchdata to a compatible release or upgrade DGL.
- Backend errors often come from missing PyTorch/MXNet/TensorFlow, incompatible CUDA wheels, or stale backend config.

## Backend And Device Mismatch

Symptoms:

- Tensors live on CPU while graph lives on CUDA, or the reverse.
- `num_workers > 0` with CUDA sampling fails.
- UVA sampling is requested but train IDs are not on GPU.

Route:

- For graph object/device basics, use `sub-skills/graph-apis/`.
- For dataloading, GPU sampling, and UVA, use `sub-skills/dataloading-graphbolt/`.
- For model-layer tensors and training loops, use `sub-skills/message-passing-training/`.

Recovery:

1. Print graph device, tensor devices, and selected backend.
2. Keep CPU-only workflows entirely CPU unless CUDA is explicitly required.
3. For classic GPU neighbor sampling, put graph and seed IDs on GPU and set dataloader `num_workers=0`.
4. For UVA, keep graph pinned on CPU, put seed IDs on GPU, set `use_uva=True`, and set `num_workers=0`.

## Dataset, Cache, And CSV Failures

Symptoms:

- `CSVDataset` cannot find `meta.yaml` or referenced CSVs.
- CSV feature parsing fails on empty strings or inconsistent list lengths.
- Custom `DGLDataset.load()` fails after `has_cache()` returns true.
- Downloading built-in datasets is slow or blocked.

Recovery:

- Run `sub-skills/datasets-and-io/scripts/csv_dataset_linter.py DATASET_DIR` before `CSVDataset`.
- Make `has_cache()` check every file that `load()` requires.
- Use `DGL_DOWNLOAD_DIR` to control cache location and `DGL_REPO` for alternate DGL data mirrors when appropriate.
- Do not assume downloadable dataset tests are safe in restricted environments.

## Message Passing And Layer Errors

Symptoms:

- `GraphConv` or `GATConv` complains about zero in-degree nodes.
- `HeteroGraphConv` relation keys do not match graph canonical etypes.
- Missing `feat`, `label`, `train_mask`, `val_mask`, or `test_mask` in `ndata`/`edata`.
- Sparse operations fail to import or produce unexpected shapes.

Recovery:

- Route layer and training details to `sub-skills/message-passing-training/`.
- Add self-loops when valid for the graph, or use layer options such as `allow_zero_in_degree=True` when the model semantics permit it.
- Validate feature and mask names before entering the training loop.
- Smoke-check `dgl.sparse` before depending on sparse workflows.

## Distributed Workflow Hazards

Symptoms:

- Partition config paths are missing or absolute to a different machine.
- `ip_config.txt` host count does not match `num_parts`.
- Edge type keys are relation-only strings instead of canonical `src:rel:dst` strings.
- Launch commands would SSH, start servers, or mutate shared workspaces.

Recovery:

- Route to `sub-skills/distributed-tools/`.
- Run `scripts/check_partition_config.py` in that sub-skill for read-only JSON/path preflight.
- Use `scripts/dgl_distributed_command_builder.py` to print a command for review; do not execute it until the user confirms SSH, shared storage, ports, and cleanup plan.

## DGL-Go Config And Runtime Failures

Symptoms:

- `dgl` command is missing or not the DGL-Go CLI.
- YAML has an unknown `pipeline_name` or missing `data`, `model`, or `general_pipeline` sections.
- Custom CSV DGL-Go config lacks `data_path` or split/mask strategy.
- Training downloads datasets, imports optional packages, or fails loading a checkpoint.

Recovery:

- Route to `sub-skills/dglgo-cli/`.
- Run `scripts/dglgo_config_linter.py CFG.yaml` before `dgl train` or `dgl export`.
- Prefer `dgl export --cfg CFG.yaml --output SCRIPT.py` before long or unfamiliar training runs.
- Use `sub-skills/datasets-and-io/` to validate custom CSV data folders.
