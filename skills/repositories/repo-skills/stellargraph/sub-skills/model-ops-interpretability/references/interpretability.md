# Interpretability

## Scope

StellarGraph includes saliency and integrated-gradient helpers for explaining
node classification models, especially GCN and GAT variants. Use this route
after a differentiable Keras model has been built with a compatible full-batch
generator.

## Integrated gradients

`IntegratedGradients(model, generator)` expects a Keras model and the matching
full-batch sequence/generator output. Dense and sparse paths have different
input-count expectations:

- dense full-batch model: features, node indices, dense adjacency;
- sparse full-batch model: features, node indices, sparse adjacency indices,
  sparse adjacency values.

Important methods include:

- `get_integrated_node_masks(node_idx, class_of_interest, features_baseline=None, steps=20)`;
- `get_integrated_link_masks(node_idx, class_of_interest, non_exist_edge=False, adj_baseline=None, steps=20)`;
- `get_node_importance(node_idx, class_of_interest, steps=20)`.

## GCN/GAT saliency

The GCN/GAT saliency modules specialize gradient-style explanations for those
model families. Use the same graph, generator, sparse/dense setting, and class
index that were used to build the model.

## Practical workflow

1. Train or load a compatible node classification model.
2. Keep the generator object and sequence used to build the model.
3. Select target node indices and class indices explicitly.
4. Compute feature or edge masks.
5. Map internal indices back to graph node IDs when presenting results.

## Cautions

- Vanilla gradients can be misleading for discrete graph structure; integrated
  gradients mitigate some of this by interpolating from a baseline.
- Edge importance for nonexistent edges and existing edges use different
  baselines; choose `non_exist_edge` deliberately.
- Do not mix dense and sparse generator/model paths.
