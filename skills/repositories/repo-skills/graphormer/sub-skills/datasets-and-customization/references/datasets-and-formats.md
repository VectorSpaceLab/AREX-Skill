# Dataset sources and formats

Graphormer’s dataset path has two layers:
1. a built-in lookup path for DGL, PyG, and OGB datasets
2. a custom registration path for user modules under `--user-data-dir`

## Built-in dataset sources

The built-in lookup path recognizes these sources:

- `dgl`
- `pyg`
- `ogb`

Use a single dataset-name string. When extra options are needed, use:

```text
dataset_name:param=value,param2=value2
```

If a parameter value is a list, join the list items with `+`:

```text
qm9:label_keys=mu+alpha+homo
```

### DGL source

Common DGL names:

- `qm7b`
- `qm9`
- `qm9edge`
- `minigc`
- `tu`
- `gin`
- `fakenews`

Typical parameter patterns:

- `qm9:label_keys=mu+alpha+homo,cutoff=5.0`
- `qm9edge:label_keys=mu+alpha+homo`
- `minigc:num_graphs=100,min_num_v=10,max_num_v=20,seed=0`
- `tu:name=MUTAG`
- `gin:name=MUTAG,self_loop=true,degree_as_nlabel=false`
- `fakenews:name=politifact,feature_name=spacy`

Notes:
- DGL wrappers support random 70/20/10 splits when a source dataset does not provide explicit splits.
- Graphormer only uses integer node and edge features in the DGL path.
- Heterogeneous DGL graphs are not supported by the Graphormer DGL wrapper.

### PyG source

Common PyG names:

- `qm7b`
- `qm9`
- `zinc`
- `moleculenet`

Typical parameter patterns:

- `moleculenet:name=bbbp`

Notes:
- `zinc` uses source-provided train/val/test subsets.
- Other PyG datasets fall back to Graphormer’s internal split logic when explicit splits are not supplied.
- Integer node and edge features are the only features carried forward into Graphormer preprocessing.

### OGB source

Common OGB names:

- `ogbg-molhiv`
- `ogbg-molpcba`
- `pcqm4m`
- `pcqm4mv2`

Notes:
- OGB datasets already provide split metadata; Graphormer reads it from the source dataset.
- `pcqm4mv2` uses `train`, `valid`, and `test-dev` indices in the wrapper.
- OGB names do not need extra `param=value` suffixes in the current Graphormer code path.

## Custom datasets

Custom datasets are the right choice when you want a custom split, a dataset object that already exists in memory, or a user-defined loader.

Rules:

- Put the module in a directory passed to `--user-data-dir`.
- Do not combine `--user-data-dir` with `--dataset-source`.
- Register each dataset with `@register_dataset("name")`.
- Return a dictionary with these keys:
  - `dataset`
  - `train_idx`
  - `valid_idx`
  - `test_idx`
  - `source`
- Set `source` to `dgl` or `pyg`.

The registration function runs during module import. Any work done inside the function happens immediately, so keep the registration body lightweight and deterministic.

## Preprocessing and batching

Graphormer preprocessing expects graph items that can be converted into the following fields:

- `idx`
- `attn_bias`
- `attn_edge_type`
- `spatial_pos`
- `in_degree`
- `out_degree`
- `x`
- `edge_input`
- `y`

Batch-time behavior:

- `max_nodes` drops graphs whose node count is too large for the batch.
- `spatial_pos_max` masks far-away positions with `-inf` in attention bias.
- `multi_hop_max_dist` truncates the multi-hop edge history.

## Validation checklist

1. Confirm the source family: DGL, PyG, OGB, or custom registration.
2. Write the exact `dataset_name:param=value` string, if parameters are needed.
3. For custom datasets, return the required split indices and set `source` to `dgl` or `pyg`.
4. Keep node and edge features integer-coded.
5. Validate the custom module with the bundled helper before training.
