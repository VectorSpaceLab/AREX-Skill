# Cross-Cutting Troubleshooting

## `ModuleNotFoundError: No module named 'torch'`

Likely cause: `torch-geometric` is installed but PyTorch is not installed in the active environment.

Recovery:

1. Install a PyTorch build compatible with the current Python and hardware.
2. Run `python scripts/check_pyg_environment.py --require-torch --require-pyg --json`.
3. Re-run the relevant sub-skill smoke script.

## `ModuleNotFoundError: No module named 'torch_geometric'`

Likely cause: PyG is not installed in the environment used by the agent or script.

Recovery:

```bash
python -m pip install torch-geometric
python - <<'PY'
import torch_geometric
print(torch_geometric.__version__)
PY
```

If working on a PyG checkout, use an editable install only in a private development environment.

## Optional Sampler or Sparse Backend Missing

Symptoms include neighbor sampling failures, messages about `pyg-lib` or `torch-sparse`, or slow sparse paths.

Recovery:

- Run `python scripts/check_pyg_environment.py --require-neighbor-backend --json`.
- Install optional PyG extension wheels matching the active PyTorch and backend.
- If the user only needs `DataLoader` over small independent graphs, do not install sampling extensions; use the loaders sub-skill's basic batching path.

## CPU/GPU Wheel Mismatch

Symptoms include import errors from compiled extensions, CUDA symbol errors, `torch.cuda.is_available()` unexpectedly false, or extension wheels tagged for a different PyTorch/CUDA version.

Recovery:

1. Check `torch.__version__`, `torch.version.cuda`, and `torch.cuda.is_available()`.
2. Confirm optional PyG extension wheels match the same PyTorch and CUDA runtime.
3. Prefer CPU wheels when the workflow is data/model authoring and does not need GPU execution.
4. Do not mix CPU PyTorch with CUDA-only extension wheels.

## Dataset Downloads or Network Failures

Many public examples instantiate datasets that download files. For skill-driven checks, prefer bundled synthetic scripts under sub-skills. If the user explicitly needs a public dataset:

- Choose a writable `root` directory.
- Confirm network access and expected dataset size.
- Separate download/processing failures from model or loader failures.
- Cache processed data deliberately and use `force_reload=True` only when reprocessing is intended.

## Shape, Mask, and Metadata Failures

- `edge_index` should be a two-row `torch.long` tensor.
- Node feature rows should match `num_nodes` unless `num_nodes` is explicitly set.
- Supervision masks must index the same node, edge, or graph dimension used for loss.
- Heterogeneous edge types must be explicit `(source_type, relation_type, destination_type)` triplets.
- For hetero link prediction, record forward and reverse relation pairs before splitting.

Route detailed fixes to the owning sub-skill: data validation, loaders/sampling, GNN modeling, hetero graphs, explainability, scalable/distributed, or GraphGym.

## GraphGym Optional Dependencies

GraphGym workflows may need packages such as `yacs`, PyTorch Lightning, protobuf constraints, and YAML parsing. Use the GraphGym validator to inspect config shape before installing broad extras or launching training.

## When to Refresh This Skill

Refresh if PyG source code, public docs, examples, tests, optional dependencies, or package version have changed since `references/repo-provenance.md`. Do not patch stale API details manually unless the refresh workflow is not available.
