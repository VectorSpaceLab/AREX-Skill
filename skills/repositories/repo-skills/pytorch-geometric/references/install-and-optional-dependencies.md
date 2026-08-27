# Install and Optional Dependencies

## When to Read

Read this before installing PyTorch Geometric, diagnosing imports, choosing CPU/GPU wheels, or deciding which optional dependency group belongs to a workflow.

## Baseline Package Facts

- Distribution: `torch-geometric`.
- Import package: `torch_geometric`.
- Verified package version for this skill snapshot: `2.9.0`.
- Supported Python from package metadata: `>=3.10`.
- PyG imports `torch`, but the base package metadata does not install `torch` for you. Install a compatible PyTorch build first.
- Base dependencies include common Python utilities such as `aiohttp`, `fsspec`, `jinja2`, `numpy`, `psutil`, `pyparsing`, `requests`, `tqdm`, and `xxhash`.

## Minimal CPU Setup

```bash
python -m pip install torch
python -m pip install torch-geometric
python - <<'PY'
import torch
import torch_geometric
print(torch.__version__)
print(torch_geometric.__version__)
PY
```

Use the PyTorch installation selector for the target platform when the default `pip install torch` is not appropriate. Keep the PyTorch version, Python version, CUDA/ROCm runtime, and optional PyG extension wheels compatible.

## Optional Groups and When to Use Them

| Optional area | Typical need | Install only when |
| --- | --- | --- |
| GraphGym | YAML experiment management, registry customization, run-single/run-batch workflows | The task uses GraphGym config files or `torch_geometric.graphgym` APIs |
| model hub | Hugging Face model hub integration | The task publishes or loads models via hub APIs |
| benchmark | benchmark plots, wandb, pandas, networkx-heavy benchmark reports | The task explicitly runs benchmark tooling |
| RAG/LLM | graph retrieval, LLM model wrappers, vector/RAG utilities | The task uses `torch_geometric.llm` or examples requiring model downloads/services |
| test/dev | upstream tests, ONNX checks, linters, pre-commit | The task is repo maintenance, not normal PyG usage |
| full | broad scientific/data/explainer optional stack | A selected workflow genuinely requires multiple optional integrations |

## Optional PyG Extension Wheels

Some loader, sampler, sparse, and performance paths may require or benefit from packages such as `pyg-lib`, `torch-sparse`, `torch-scatter`, `torch-cluster`, or `torch-spline-conv`. Install them from PyG/PyTorch-compatible wheels that match:

- Python version.
- PyTorch version.
- CPU vs CUDA/ROCm backend.
- CUDA runtime tag when using GPU wheels.

If a neighbor sampling workflow fails because no backend is available, route to `sub-skills/scalable-distributed/scripts/check_sampling_backends.py` or `sub-skills/loaders-and-sampling/scripts/loader_smoke_test.py` for diagnostics before changing model code.

## Safe Setup Policy

- Do not install all extras by default. Select the smallest dependency set that matches the requested workflow.
- Do not start dataset downloads, benchmark runs, GraphGym training, distributed workers, or multi-GPU jobs as installation checks.
- Use import/signature checks and tiny synthetic scripts first.
