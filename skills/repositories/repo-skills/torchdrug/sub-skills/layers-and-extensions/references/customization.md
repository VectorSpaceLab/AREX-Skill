# Customization Patterns

Use these patterns to implement new TorchDrug layers or reusable representation models without breaking config serialization, packed graph behavior, or task integration.

## Custom Message Passing Layers

Subclass `layers.MessagePassingBase` for node-to-node graph layers. Implement these methods:

- `message(graph, input)`: return one message row per edge, shape `(|E|, feature_dim...)`.
- `aggregate(graph, message)`: reduce edge messages to one update row per node, shape `(|V|, output_dim...)`.
- `combine(input, update)`: combine previous node states and updates into output node states.
- Optionally override `message_and_aggregate(graph, input)` for fused sparse matrix/scatter implementations.

A PageRank-like layer should gather source nodes from `graph.edge_list[:, 0]`, aggregate to target nodes from `graph.edge_list[:, 1]`, and set `dim_size=graph.num_node` in scatter operations so isolated nodes are preserved. Use `graph.device` for new tensors and avoid CPU tensors inside GPU graphs.

## Scatter and Variadic Safety

TorchDrug relies on packed tensors instead of padding. Common packed fields are `graph.node2graph`, `graph.edge2graph`, `graph.num_nodes`, `graph.num_edges`, and cumulative offsets.

Use `torchdrug.layers.functional` helpers when each graph has a different number of elements:

- `variadic_sum(input, size)`, `variadic_mean(input, size)`, and `variadic_max(input, size)` for per-graph reductions.
- `variadic_softmax(input, size)` and `variadic_log_softmax(input, size)` for logits grouped by graph/item.
- `variadic_cross_entropy(input, target, size)` for one target index per variadic group.
- `variadic_topk(input, size, k)`, `variadic_sort(input, size)`, and `variadic_sample(input, size, num_sample)` for grouped selection.
- `variadic_arange(size)`, `variadic_meshgrid(input1, size1, input2, size2)`, and `multi_slice_mask(starts, ends, length=None)` for constructing packed indices and masks.
- `variadic_to_padded(input, size, value=0)` only when a dense representation is actually needed.

The invariant is `input.shape[0] == size.sum()`. If you index into packed values, keep all indexes on the same device and use `long` dtype.

## Readout and Broadcast Patterns

Readout maps node/edge/residue features to graph features. Broadcast maps graph features back to node/edge/residue rows by indexing with `node2graph`, `edge2graph`, or `residue2graph`.

- Use `layers.SumReadout`, `layers.MeanReadout`, or `layers.MaxReadout` for standard graph reductions.
- Use `layers.AttentionReadout(input_dim)` when the model should learn which nodes/residues matter.
- Use `layers.Set2Set(input_dim)` when order-sensitive set processing is desired; remember the output dimension is `2 * input_dim`.
- For custom variance/normalization-style features, scatter graph means with `dim_size=graph.batch_size`, then broadcast with `mean[graph.node2graph]`.

## Custom Representation Models

Reusable TorchDrug representation models should follow the existing model contract:

- Inherit `nn.Module` and `core.Configurable` in the concrete class.
- Register with `@R.register("models.MyModel")` from `torchdrug.core import Registry as R` if config/YAML reconstruction should work.
- Store `self.input_dim` and `self.output_dim`; add `self.node_output_dim` when node and graph dimensions differ.
- Accept `forward(self, graph, input, all_loss=None, metric=None)` for graph encoders. Knowledge-graph scoring models instead commonly accept `forward(graph, h_index, t_index, r_index, all_loss=None, metric=None)`.
- Return a dictionary with explicit keys such as `"node_feature"`, `"graph_feature"`, `"edge_feature"`, or `"residue_feature"`.
- If the model contributes auxiliary losses, mutate only when `all_loss is not None`; record scalar tensors in `metric` with stable names.

Example output contract for graph encoders:

```python
return {
    "graph_feature": graph_feature,
    "node_feature": node_feature,
}
```

## Configurable Requirements

`core.Configurable` records constructor arguments automatically through the class `__init__` signature. To keep this reliable:

- Put every reconstructable hyperparameter in `__init__`; avoid hidden global state.
- Use serializable values or nested `Configurable` instances for constructor arguments.
- Re-declare `core.Configurable` on derived custom classes; it applies to the current concrete class.
- Register classes with a stable key such as `models.MyEncoder` or `layers.MyGraphConstruction` if they should load from config dicts.
- Avoid passing live dataset objects, file handles, or device-specific tensors as constructor arguments unless you implement custom load/config logic.

## Registry Conventions

- `R.register("models.Name")` exposes a class for `R.search("Name")` and `core.Configurable.load_config_dict`.
- Use unique hierarchical names; registering the same key twice raises an error.
- Short searches can be ambiguous if multiple registered keys contain the same token; prefer canonical names in saved configs.
- Existing public namespaces include `models.*`, `tasks.*`, `layers.GraphConstruction`, and `layers.geometry.*`.

## `all_loss` and `metric` Conventions

TorchDrug tasks usually create `all_loss = torch.tensor(0, dtype=torch.float32, device=self.device)` and `metric = {}` before calling a model. Custom models should cooperate with this pattern:

- Add differentiable auxiliary terms with `all_loss += weight * loss`.
- Put detached or raw scalar tensors in `metric` with human-readable names, for example `metric["variational regularization loss"] = loss`.
- Do not create a new metric dict inside the model if one is supplied.
- Allow inference calls with `all_loss=None` and `metric=None` without computing expensive training-only losses.

## Extending Graph Construction

To customize protein/geometric graph construction, subclass `layers.GraphConstruction` and define `edge_<name>(self, graph, edge_list, num_relation)`. Then instantiate with `edge_feature="<name>"`. The returned edge feature tensor must have first dimension equal to the new graph's edge count.

Use node/edge layer modules from `torchdrug.layers.geometry` for common operations:

- Edge modules: `BondEdge`, `KNNEdge`, `SpatialEdge`, `SequentialEdge`.
- Node modules: `AlphaCarbonNode`, `IdentityNode`, `RandomEdgeMask`, `SubsequenceNode`, `SubspaceNode`.
- `SpatialLineGraph(num_angle_bin=8)` for edge-angle relation graphs used by GearNet-style geometric relational layers.

Route the actual creation of `Molecule`, `Protein`, `PackedGraph`, and feature fields to the graph-data sub-skill.
