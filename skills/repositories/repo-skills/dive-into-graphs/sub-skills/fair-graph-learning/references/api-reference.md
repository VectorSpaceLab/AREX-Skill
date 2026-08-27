# Fair Graph Learning API Reference

## Datasets

- `NBA(data_path='https://...', root='./dataset/nba')`.
- `POKEC(data_path='https://...', root='./dataset/pokec', dataset_sample='pokec_z')`.

## Runner and Model Surface

- `run()` returns the Graphair training/evaluation driver.
- `graphair(aug_model, f_encoder, sens_model, classifier_model, lr=1e-4, weight_decay=1e-5, alpha=0.1, beta=1.0, gamma=10.0, lam=1.0, dataset='POKEC', num_hidden=64, num_proj_hidden=64)`.
- `aug_module`, `GCN_Body`, `GCN`, and `Classifier` are the model-building blocks used by the runner.

## Utilities

Import these from `dig.fairgraph.utils.utils`:

- `accuracy(output, labels)`.
- `fair_metric(output, idx, labels, sens)`.
- `scipysp_to_pytorchsp(sp_mx)`.
