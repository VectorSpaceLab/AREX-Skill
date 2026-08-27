# GraphBolt Data Formats

GraphBolt `OnDiskDataset` uses `metadata.yaml`, not DGL `CSVDataset`'s `meta.yaml`. Use this reference for the GraphBolt large-graph/minibatch format and route raw CSV validation to `../datasets-and-io/`.

## Directory Layout

A practical dataset directory looks like this:

```text
my_graphbolt_dataset/
  metadata.yaml
  edges/
    paper-cites-paper.npy
  features/
    paper-feat.npy
  sets/
    train-seeds.npy
    train-labels.npy
    valid-seeds.npy
    valid-labels.npy
    test-seeds.npy
    test-labels.npy
```

All paths in `metadata.yaml` should be relative to the directory containing the metadata file. Avoid absolute paths in reusable datasets.

## Raw `metadata.yaml` Schema

Raw metadata can describe graph structure, feature tensors, and task splits. `OnDiskDataset` preprocesses graph structure into a `FusedCSCSamplingGraph` cache when needed.

```yaml
dataset_name: my_graphbolt_dataset
graph:
  nodes:
    - type: paper
      num: 1000
  edges:
    - type: paper:cites:paper
      format: numpy
      path: edges/paper-cites-paper.npy
feature_data:
  - domain: node
    type: paper
    name: feat
    format: numpy
    in_memory: true
    path: features/paper-feat.npy
tasks:
  - name: node_classification
    num_classes: 3
    train_set:
      - type: paper
        data:
          - name: seeds
            format: numpy
            in_memory: true
            path: sets/train-seeds.npy
          - name: labels
            format: numpy
            in_memory: true
            path: sets/train-labels.npy
    validation_set:
      - type: paper
        data:
          - name: seeds
            format: numpy
            path: sets/valid-seeds.npy
          - name: labels
            format: numpy
            path: sets/valid-labels.npy
    test_set:
      - type: paper
        data:
          - name: seeds
            format: numpy
            path: sets/test-seeds.npy
          - name: labels
            format: numpy
            path: sets/test-labels.npy
```

## Top-Level Fields

| Field | Required | Meaning |
| --- | --- | --- |
| `dataset_name` | No | Human-readable dataset name exposed as `dataset.dataset_name`. |
| `graph` | Optional for task-only checks | Raw graph topology before preprocessing. Contains `nodes` and `edges`. |
| `graph_topology` | Optional alternative | Preprocessed topology entry with `type: FusedCSCSamplingGraph` and `path`. |
| `feature_data` | No | List of node, edge, or graph feature tensor descriptors. |
| `tasks` | No | List of training/evaluation task descriptors. |

A loaded training dataset usually has either `graph` before preprocessing or `graph_topology` after preprocessing, plus at least one task split.

## Graph Structure Fields

`graph.nodes` is a list of node-type entries:

| Field | Required | Meaning |
| --- | --- | --- |
| `type` | No for homogeneous, yes for heterograph | Node type string. Omit or use `null` only for homogeneous single-type graphs. |
| `num` | Yes | Number of nodes for that type. |

`graph.edges` is a list of edge-type entries:

| Field | Required | Meaning |
| --- | --- | --- |
| `type` | No for homogeneous, yes for heterograph | Edge type string. For heterographs use `src_type:relation:dst_type`. |
| `format` | Yes | `csv` or `numpy` for raw graph edges. `numpy` is recommended for large graphs. |
| `path` | Yes | Relative path to edge data. |

Edge data assumptions:

- `numpy` graph edges should represent source/destination rows and are commonly shaped `(2, num_edges)`.
- `csv` graph edges should contain source and destination columns consumable by GraphBolt preprocessing.
- Edges are directed. Add reverse edges explicitly if the model expects bidirectional message flow.
- For heterographs, node IDs inside each edge file are local to the source and destination node types named in the edge type string.

## Preprocessed `graph_topology`

After preprocessing, metadata may replace `graph` with:

```yaml
graph_topology:
  type: FusedCSCSamplingGraph
  path: preprocessed/fused_csc_sampling_graph.pt
```

`gb.OnDiskDataset(...).load()` reads this object as `dataset.graph`. Do not edit this by hand unless you produced the file with GraphBolt-compatible preprocessing.

## `feature_data` Fields

Each feature descriptor has these canonical fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `domain` | Yes | `node`, `edge`, or `graph` in current source models; node/edge are the common training cases. |
| `type` | No for homogeneous | Node type or edge type string. Use `src:rel:dst` for heterograph edge features. |
| `name` | Yes | Feature name used by `fetch_feature()`, such as `feat`, `label`, or `weight`. |
| `format` | Yes | `numpy` or `torch`. |
| `path` | Yes | Relative path to the feature tensor file. |
| `in_memory` | No | Defaults to `true`; set `false` for large disk-backed features. |

Shape rules:

- Node feature row count should equal `num` for its node type.
- Edge feature row count should equal the number of edges for its edge type.
- Heterogeneous features with the same `name` should cover all required types when the model fetches that feature for all types.
- Extra fields are preserved as metadata on feature objects; use them for dataset-specific annotations, not for required loading behavior unless your runtime supports them.

## Task and Split Fields

Each task entry may include `name`, `num_classes`, and arbitrary metadata, plus split fields:

```yaml
tasks:
  - name: link_prediction
    train_set:
      - type: user:likes:item
        data:
          - name: seeds
            format: numpy
            path: sets/train-pairs.npy
          - name: labels
            format: numpy
            path: sets/train-labels.npy
          - name: indexes
            format: numpy
            path: sets/train-indexes.npy
    validation_set: []
    test_set: []
```

Split fields:

- `train_set`, `validation_set`, and `test_set` are lists. Empty lists are allowed when a split is absent.
- Each split item has optional `type` plus a `data` list.
- Homogeneous datasets should have at most one split item with omitted or `null` `type`.
- Heterogeneous datasets use one split item per node type or edge type.

Each `data` entry has:

| Field | Required | Meaning |
| --- | --- | --- |
| `name` | Usually yes | MiniBatch field name. Common values are `seeds`, `labels`, and `indexes`. |
| `format` | Yes | `numpy` or `torch`. |
| `path` | Yes | Relative path to the tensor file. |
| `in_memory` | No | Defaults to `true`; set `false` for large split arrays. |

Task data names control `MiniBatch` mapping:

- `seeds`: seed nodes for node tasks or node-pair rows for link/edge tasks.
- `labels`: labels aligned with `seeds`.
- `indexes`: query/group IDs aligned with `seeds`, often used for grouped negatives or hyperedges.
- Unknown names are added as custom `MiniBatch` attributes by the default minibatcher, but this can emit warnings. Prefer a custom minibatcher for nonstandard fields.

## Homogeneous Node Classification Minimal Example

```yaml
dataset_name: tiny_homo
graph:
  nodes:
    - num: 4
  edges:
    - format: numpy
      path: edges.npy
feature_data:
  - domain: node
    name: feat
    format: numpy
    path: feat.npy
tasks:
  - name: node_classification
    num_classes: 2
    train_set:
      - data:
          - name: seeds
            format: numpy
            path: train_ids.npy
          - name: labels
            format: numpy
            path: train_labels.npy
    validation_set: []
    test_set: []
```

## Heterogeneous Link Prediction Minimal Example

```yaml
dataset_name: tiny_hetero
graph:
  nodes:
    - type: user
      num: 100
    - type: item
      num: 200
  edges:
    - type: user:likes:item
      format: numpy
      path: edges/user-likes-item.npy
    - type: item:liked-by:user
      format: numpy
      path: edges/item-liked-by-user.npy
feature_data:
  - domain: node
    type: user
    name: feat
    format: numpy
    path: features/user-feat.npy
  - domain: node
    type: item
    name: feat
    format: numpy
    path: features/item-feat.npy
tasks:
  - name: link_prediction
    train_set:
      - type: user:likes:item
        data:
          - name: seeds
            format: numpy
            path: sets/train-pairs.npy
    validation_set: []
    test_set: []
```

## Metadata Validation Checklist

Before calling `gb.OnDiskDataset(dataset_dir).load()`:

- The file is named `metadata.yaml` or the explicit path points to a metadata file accepted by the installed DGL version.
- All paths are relative and exist under the dataset directory.
- Every graph node entry has `num`.
- Every graph edge entry has `format` and `path`.
- Every feature entry has `domain`, `name`, `format`, and `path`.
- Every split data entry has `format` and `path`; use `name` unless a custom minibatcher handles unnamed fields.
- The first dimension of `seeds`, `labels`, and `indexes` files matches within a split item.
- Heterograph edge type strings use exactly three colon-separated parts.
- Use `python scripts/graphbolt_pipeline_sanity.py --metadata metadata.yaml` from this sub-skill directory for a shallow deterministic check.

## Common Handoffs

From `../datasets-and-io/` to this sub-skill, ask for:

- Dataset directory containing `metadata.yaml` and relative tensor files.
- Target task name and split to load.
- Feature names to fetch per node/edge type.
- Whether disk-backed features should remain `in_memory: false`.
- Whether the next step should use GraphBolt or classic `dgl.dataloading.DataLoader`.

From this sub-skill to `../message-passing-training/`, provide:

- Number of GNN layers and fanouts.
- Whether minibatches yield classic tuples or GraphBolt `MiniBatch` objects.
- The feature keys and label fields already present in each minibatch.
- Device placement assumptions for features, labels, blocks, and model parameters.
