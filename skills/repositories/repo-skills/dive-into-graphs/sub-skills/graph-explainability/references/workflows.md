# Graph Explainability Workflows

## Single-Instance Explanation

1. Train or load a base GNN.
2. Pick an explainer that matches the explanation target: edge masks, node masks, or subgraph search.
3. Run the explainer on a node index, graph index, or edge target.
4. Convert the output into the shape expected by downstream metrics.

## Metric Computation

1. Create a collector with the target sparsity.
2. Use `ExplanationProcessor` to apply the masks to the model and collect related predictions.
3. Read the resulting fidelity, fidelity-inverse, sparsity, accuracy, and stability values from `XCollector`.

## Benchmark-Style Workflows

- Use synthetic BA motifs such as BA-shapes or BA-LRP when you need ground-truth explanation structure.
- Use molecule or sentiment datasets when you need real-graph behavior and no synthetic motif labels.
- When a saved model checkpoint comes from a different PyG release, adapt the state dict with `compatible_state_dict` before loading.
