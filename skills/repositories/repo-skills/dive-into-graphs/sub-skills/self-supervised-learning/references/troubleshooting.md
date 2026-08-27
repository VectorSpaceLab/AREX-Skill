# Self-Supervised Learning Troubleshooting

## Dataset Download or Cache Surprises

- `get_dataset` and `get_node_dataset` may download data into the chosen root.
- If you only want routing guidance, use the bundled smoke script or inspect the API reference first.

## Wrong Representation Level

- `GraphCL`, `InfoGraph`, and `GraphUnsupervised` are typically graph-level workflows.
- `GRACE` and `NodeMVGRL` are node-level workflows.
- If the encoder returns the wrong shape, check `node_level`, `graph_level`, and the projection-head dimensions.

## Contrastive Objective Errors

- `NCE_loss` and `JSE_loss` expect the right combination of `zs`, `zs_n`, `batch`, and `sigma` arguments.
- If `neg_by_crpt=True`, use the JSE path and not `NCE`.
- When using custom views, make sure each view function returns tensors compatible with the encoder.

## Evaluation Noise

- SSL evaluators call downstream classifiers and can vary run-to-run.
- Fix the seed with `setup_seed` before comparing configurations.
