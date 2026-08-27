# Self-Supervised Learning Workflows

## Graph-Level SSL

1. Choose a TU dataset with `get_dataset` or a dataset-specific loader.
2. Build an `Encoder` with the right feature dimension and a graph-level representation size.
3. Select one or more augmentations: `dropN`, `permE`, `subgraph`, `maskN`, or a `RandomView` composition.
4. Use `GraphCL` for augmentation-based contrastive pretraining, `InfoGraph` for node-global MI maximization, or `MVGRL` for diffusion-based views.
5. Evaluate the learned representation with `GraphUnsupervised` or `GraphSemisupervised`.

## Node-Level SSL

1. Load `get_node_dataset` such as Cora.
2. Build an encoder with `node_level=True`.
3. Select `GRACE` or `NodeMVGRL` and configure the augmentations.
4. Evaluate with `NodeUnsupervised`.

## Custom Contrastive Methods

- Use `Contrastive` when the built-in wrappers are too narrow.
- Pair your own view functions with the appropriate objective (`NCE` or `JSE`).
- If using node-level and graph-level outputs together, confirm the encoder returns the expected tuple shape before training.
