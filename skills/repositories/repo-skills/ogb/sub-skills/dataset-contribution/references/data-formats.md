# Dataset contribution data formats

## Homogeneous graph format

Each graph dictionary should provide:

- `edge_index` with shape `(2, num_edges)`
- `num_nodes` as an integer
- optional `node_feat` with shape `(num_nodes, node_feat_dim)`
- optional `edge_feat` with shape `(num_edges, edge_feat_dim)`

## Heterogeneous graph format

Each graph dictionary should provide:

- `edge_index_dict`
- `num_nodes_dict`
- optional `node_feat_dict`
- optional `edge_feat_dict`

The keys must match the entity/relation types used by the dataset.

## Label format

- Graph and node labels use NumPy arrays.
- Node labels for heterogeneous datasets may be dictionaries keyed by node type.
- Link datasets do not need target labels.

## Mapping directory

The mapping directory must contain `README.md` and any other metadata files the
release needs. The export helper copies the directory into the packaged
release.

## Split format

The split dictionary must contain `train`, `valid`, and `test` keys.

## Metadata file

`meta_dict.pt` is the final handoff object used by the loaders. It records the
release version, directory path, binary-vs-CSV mode, evaluation metric, and
other dataset metadata.
