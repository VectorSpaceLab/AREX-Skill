# Spektral API Overview

Spektral is organized around graph containers and loaders feeding Keras/TensorFlow graph layers and models. The package version inspected for this skill is `1.3.1`.

## Module map

| Module | Public surface | Route |
| --- | --- | --- |
| `spektral.data` | `Graph`, `Dataset`, `Loader`, `SingleLoader`, `DisjointLoader`, `BatchLoader`, `PackedBatchLoader`, `MixedLoader`, and data conversion helpers | `sub-skills/graph-data/` |
| `spektral.datasets` | Citation networks, DBLP, Flickr, GraphSAGE/PPI/Reddit, MNIST grid graphs, ModelNet, OGB wrapper, QM7/QM9, and TUDataset | `sub-skills/graph-data/` |
| `spektral.transforms` | `AdjToSpTensor`, `ClusteringCoeff`, `Constant`, `Degree`, `Delaunay`, `GCNFilter`, `LaplacianPE`, `LayerPreprocess`, normalization transforms, and one-hot label transforms | `sub-skills/graph-data/` |
| `spektral.layers` | Base graph layers, convolution/message-passing layers, global and selection pooling layers, sparse/masking helpers | `sub-skills/gnn-models/` |
| `spektral.models` | `GCN`, `GeneralGNN`, `GNNExplainer` | `sub-skills/gnn-models/` |
| `spektral.utils` | Convolution/math helpers, sparse conversion, graph I/O, Keras serialization helpers, logging, and miscellaneous encoding/padding utilities | Shared; graph math primarily belongs to `gnn-models`, data serialization belongs to `graph-data` |

## Verified key signatures

| Object | Signature |
| --- | --- |
| `Graph` | `(x=None, a=None, e=None, y=None, **kwargs)` |
| `Dataset` | `(transforms=None, **kwargs)` |
| `SingleLoader` | `(dataset, epochs=None, sample_weights=None)` |
| `DisjointLoader` | `(dataset, node_level=False, batch_size=1, epochs=None, shuffle=True)` |
| `BatchLoader` | `(dataset, mask=False, batch_size=1, epochs=None, shuffle=True, node_level=False)` |
| `GCNConv` | `(channels, activation=None, use_bias=True, kernel_initializer='glorot_uniform', bias_initializer='zeros', kernel_regularizer=None, bias_regularizer=None, activity_regularizer=None, kernel_constraint=None, bias_constraint=None, **kwargs)` |
| `GeneralConv` | `(channels=256, batch_norm=True, dropout=0.0, aggregate='sum', activation='prelu', use_bias=True, kernel_initializer='glorot_uniform', bias_initializer='zeros', kernel_regularizer=None, bias_regularizer=None, activity_regularizer=None, kernel_constraint=None, bias_constraint=None, **kwargs)` |
| `MessagePassing` | `(aggregate='sum', **kwargs)` |
| `GCN` | `(n_labels, channels=16, activation='relu', output_activation='softmax', use_bias=False, dropout_rate=0.5, l2_reg=0.00025, **kwargs)` |
| `GeneralGNN` | `(output, activation=None, hidden=256, message_passing=4, pre_process=2, post_process=2, connectivity='cat', batch_norm=True, dropout=0.0, aggregate='sum', hidden_activation='prelu', pool='sum')` |

## Packaging notes

- `pyproject.toml` declares the distribution name `spektral`, package version `1.3.1`, Python `>=3.7`, and dependencies including TensorFlow, NumPy, SciPy, pandas, scikit-learn, networkx, requests, lxml, joblib, and tqdm.
- No console-script CLI entry point is declared in `pyproject.toml`; runtime workflows are Python API workflows.
- OGB examples and wrappers require an external OGB dataset object and usually the `ogb` package, which is not part of the base dependency list.
