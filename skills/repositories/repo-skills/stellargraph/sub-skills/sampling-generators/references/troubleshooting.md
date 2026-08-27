# Sampling and Generator Troubleshooting

## Wrong graph type for generator

**Symptoms**

- `expected a graph with a single node type`
- generator constructor rejects a NetworkX object
- HinSAGE/GraphSAGE generator produces unexpected feature groups

**Recovery**

- Pass a `StellarGraph` or `StellarDiGraph`, not a raw NetworkX graph.
- Use full-batch homogeneous generators only for graphs with one node type when
  the selected model requires homogeneity.
- Use HinSAGE or relational generators for heterogeneous/relational workflows.
- Return to the graph-data-loading route and print `graph.node_types` and
  `graph.edge_types` before choosing a generator.

## Node or link IDs do not match the graph

**Symptoms**

- invalid ID errors during `flow(...)` or first batch indexing
- all-zero feature rows for sampled neighbors that should exist
- target rows do not align with generator IDs

**Recovery**

- Use external node IDs by default. Do not pass integer positions unless using
  `use_ilocs=True` intentionally.
- For node tasks, ensure target index/order matches `node_ids` passed to `flow`.
- For link tasks, pass pairs of graph node IDs and ensure every endpoint exists.
- For DataFrame flows, inspect the expected index/source/target columns for the
  specific generator class.

## Sparse vs dense full-batch confusion

**Symptoms**

- Keras model expects three or four inputs but receives a different list length.
- Sparse adjacency shape errors appear in `GraphConvolution` or saliency code.

**Recovery**

- `sparse=True` full-batch sequences include sparse index/value tensors in
  addition to features and output indices.
- `sparse=False` full-batch sequences include a dense adjacency matrix.
- Build the model from the same generator instance used for `flow`; do not mix a
  sparse model with dense sequence outputs.

## `num_samples`, `in_samples`, or `out_samples` mismatch

**Symptoms**

- GraphSAGE/HinSAGE model construction fails.
- Tensor shapes are incompatible across aggregation layers.

**Recovery**

- Use one sampling count per neighborhood aggregation layer.
- For directed GraphSAGE, supply matching lists for incoming and outgoing
  neighborhoods.
- Keep model `layer_sizes` and generator sample lists aligned.

## Target shape errors

**Symptoms**

- Keras loss complains about rank or final dimension.
- Full-batch generator target output shape differs from mini-batch generator
  target shape.

**Recovery**

- Inspect `sequence[0]` before training.
- For classification, one-hot encode labels when using categorical losses.
- For binary link prediction, use a 1D or column vector target shape compatible
  with the Keras output head.
- For graph classification, targets are graph-level, not node-level.

## Random walk failures

**Symptoms**

- Walk lists are empty or shorter than requested.
- Metapath walks fail on heterogeneous graphs.
- Temporal walks fail to find context windows.

**Recovery**

- Ensure starting nodes exist and have the required type.
- Confirm each metapath transition exists in the graph schema.
- For weighted walks, verify weights exist and are positive where required.
- For temporal walks, confirm edge timestamps and feasible walk lengths.

## Diagnostic script

Run:

```bash
python sub-skills/sampling-generators/scripts/generator_shape_smoke.py
```

If it passes, the package's basic generator machinery works. Compare your real
workflow's graph types, features, IDs, sampling lists, and target shapes to the
smoke output.
