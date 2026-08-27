---
name: layers-and-extensions
description: "Choose TorchDrug graph neural network layers/models, readouts,
  variadic tensor utilities, and custom layer/model extension patterns."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TorchDrug Layers & Extensions

Use this sub-skill when a task asks you to choose or customize TorchDrug graph layers, representation models, readouts, samplers, graph construction modules, or variadic tensor utilities.

## Route First

- For graph, molecule, protein, or knowledge-graph object construction, packing, masking, or feature fields, use `../graph-data/SKILL.md`.
- For `core.Engine`, optimizer/scheduler wiring, checkpointing, YAML config persistence, or training loops, use `../training-engine/SKILL.md`.
- For complete molecular, knowledge-graph, or protein workflows, route to the relevant workflow sub-skill and use this sub-skill only for model/layer internals.

## Common Decisions

- Pick `models.GIN` or `models.GCN` for homogeneous molecular/property graphs; set `edge_input_dim` only when `graph.edge_feature` exists and has that width.
- Pick `models.RGCN`, `models.GearNet`, `layers.RelationalGraphConv`, or `layers.GeometricRelationalGraphConv` when edges carry relation ids in `edge_list[:, 2]`; ensure `graph.num_relation` equals the model/layer `num_relation`.
- Pick `models.GAT` when attention over neighbors is needed; ensure each layer `output_dim` is divisible by `num_head`.
- Pick `models.MPNN` or `models.SchNet` when continuous edge/geometric features drive messages; `MPNN` requires `edge_input_dim`.
- Use `layers.GraphConstruction` and `layers.SpatialLineGraph` for GearNet-style protein geometry before calling a GearNet-like model.
- Use `torchdrug.layers.functional.variadic_*` helpers for per-graph reductions/classification over packed irregular tensors instead of padding or Python loops.

## References

- `references/layer-and-model-api.md` lists architecture aliases, constructor parameters, readouts, samplers, graph construction layers, and model family selection notes.
- `references/customization.md` explains `MessagePassingBase`, variadic utilities, registry/configurable conventions, model output dictionaries, and `all_loss` / `metric` integration.
- `references/troubleshooting.md` maps common import, build, shape, relation, variadic, CUDA/JIT, and warning failures to concrete fixes.

## Safe Inspection Helper

Run the bundled helper in a TorchDrug environment to print live signatures and optional extension status without downloading data or models:

```bash
python scripts/inspect_layers.py --all
```

Use `python scripts/inspect_layers.py --help` to select only layers, models, geometry modules, variadic helpers, or optional imports.
