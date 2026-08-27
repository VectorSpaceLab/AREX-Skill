---
name: models-layers-and-operators
description: "Routes CogDL model registry, layer, custom GNN, and sparse
  operator workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CogDL Models, Layers, and Operators

Use this sub-skill when the user wants to pick a CogDL model name, inspect
model or layer signatures, build a custom GNN, or understand sparse/message
operator behavior.

Typical triggers:
- "Which CogDL model should I use for node classification?"
- "How do I write a custom GCN using CogDL layers?"
- "Why does an operator import or CUDA extension fail?"
- "What are the supported model names?"

Read `references/model-registry-and-layers.md` for verified model families,
layer signatures, and the registry map.
Read `references/custom-gnn.md` for the toy-graph custom GNN pattern and the
`Graph` + `BaseModel` + `GCNLayer` recipe.
Read `references/operator-compatibility.md` when sparse operators, optional
CUDA/C++ kernels, or third-party graph-library examples are involved.
Read `references/troubleshooting.md` for unknown model names, argument
registration problems, layer shape issues, and backend/build failures.

Run `scripts/inspect_model_registry.py` to print or filter the supported
model registry without touching datasets.
Run `scripts/custom_gnn_smoke.py` to build a toy `Graph` and exercise a
`GCNLayer` or `GATLayer` forward pass on CPU.

Route these elsewhere:
- `../graph-data-and-datasets/SKILL.md` for dataset schemas, masks, and
  custom fixtures.
- `../experiments-and-cli/SKILL.md` for `experiment(...)`, CLI flags, and
  AutoML orchestration.
- `../training-wrappers-and-customization/SKILL.md` for wrapper matching,
  `Trainer`, checkpoints, and logging.
- `../pipelines-and-applications/SKILL.md` for `pipeline()` apps such as
  embedding generation or OAG-BERT.

## What this sub-skill covers

- `SUPPORTED_MODELS` inspection and model-family selection.
- `build_model(args)` and `try_adding_model_args(model, parser)` behavior.
- `BaseModel` patterns for custom graph models.
- `GCNLayer`, `GATLayer`, and the `BaseLayer.forward(graph, x)` convention.
- Sparse/message operators in `cogdl.operators` and their CPU/GPU caveats.
- Optional dependency surfaces such as PyG, Jittor, DGL, or compiled
  operators when they affect model/layer use.

## Decision rules

- Choose a model family before thinking about wrappers or training config.
- If the user only needs a model list, use the registry script first and keep
  the response lightweight.
- If the user wants to add a new GNN, keep the focus on `Graph`, layers, and
  a `BaseModel` forward pass; leave data selection to the dataset sub-skill.
- Treat CUDA acceleration as optional unless the user explicitly asks for a
  GPU/operator workflow.
