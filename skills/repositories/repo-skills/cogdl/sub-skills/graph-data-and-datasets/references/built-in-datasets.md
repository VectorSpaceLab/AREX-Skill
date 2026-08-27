# Built-in Dataset Selection and Caveats

CogDL registers many datasets behind `build_dataset_from_name(name)` and the
high-level experiment API. Loading a built-in dataset is not a harmless metadata
operation: when raw or processed files are missing, dataset construction can
create cache directories, download archives/files, unpack them, and process them
into `Graph` objects.

Use built-ins only after confirming cache, network, storage, and runtime budget.
For no-download validation, build a custom `Graph` or use the bundled tiny data
script instead.

## Loading API

```python
from cogdl.datasets import build_dataset_from_name

dataset = build_dataset_from_name("cora")  # may download/write cache if absent
graph = dataset[0]
```

To control the cache root, instantiate a dataset class that accepts a data path
or use a path-aware dataset builder if the surrounding workflow already exposes
one. High-level experiment calls usually use each dataset class's default cache
root.

## Dataset cache behavior

CogDL dataset classes follow this pattern:

- `raw_file_names` describe files expected under a raw cache directory.
- `processed_file_names` describe processed files expected under a processed
  cache directory.
- Constructor logic skips download/process when those files already exist.
- If files are missing, `download()` and `process()` may run immediately.

For custom `NodeDataset` and `GraphDataset`, the single `.pt` path is the cache
artifact. Reusing a path can silently reuse older data; use a new path or remove
stale files deliberately.

## Common registered families

### Node classification

| Family | Names | Optional requirements / caveats |
| --- | --- | --- |
| Citation / Planetoid | `cora`, `citeseer`, `pubmed` | Optional network/cache. These are common quick examples but still download when absent. Node labels are single-class and use `train_mask`/`val_mask`/`test_mask`. |
| Geom / heterophily citation-like | `chameleon`, `cornell`, `film`, `squirrel`, `texas`, `wisconsin`, plus `cora_geom`, `citeseer_geom`, `pubmed_geom` | Optional network/cache. Some variants carry multiple split masks internally and select a split. |
| Large inductive / SAINT-style | `ppi`, `ppi-large`, `reddit`, `flickr`, `yelp`, `amazon-s` | Optional network/cache and larger memory/storage. Some labels are multi-label; metrics may be F1/BCE rather than accuracy/cross entropy. Train/full adjacency variants may be present. |
| Fraud / risk / dynamic collections | `Github`, `Elliptic`, `Film`, `Wiki`, `Clothing`, `Electronics`, `Dblp`, `Yelpchi`, `Alpha`, `Weibo`, `bgp`, `ssn5`, `ssn7`, `Aids`, `Nba`, `Pokec_z` | Optional network/cache. Verify masks and label conventions before training. |

### Network embedding and link-style graph data

| Family | Names | Optional requirements / caveats |
| --- | --- | --- |
| Network embedding community datasets | `ppi-ne`, `blogcatalog`, `wikipedia`, `flickr-ne`, `dblp-ne`, `youtube-ne` | Optional network/cache. Many have `x=None` and multi-hot community labels. Route embedding-model choices elsewhere. |
| Multiplex / GATNE | `amazon`, `twitter`, `youtube` | Optional network/cache. Data may contain dictionaries such as `train_data`, `valid_data`, and `test_data` rather than a simple homogeneous `edge_index`. |
| Knowledge graph | `fb13`, `fb13s`, `fb15k`, `fb15k237`, `wn18`, `wn18rr` | Optional network/cache and task-specific relation/triple fields. Route model and wrapper details to training/model sub-skills. |
| OGB link prediction | `ogbl-ppa`, `ogbl-ddi`, `ogbl-collab`, `ogbl-citation2` | Optional `ogb` Python package plus network/cache; some datasets are large. |

### Heterogeneous graph data

| Family | Names | Optional requirements / caveats |
| --- | --- | --- |
| GTN-style heterogeneous | `gtn-acm`, `gtn-dblp`, `gtn-imdb` | Optional network/cache. Data may include edge types or multiple adjacency-like fields. |
| HAN-style heterogeneous | `han-acm`, `han-dblp`, `han-imdb` | Optional network/cache. Data stores feature tensors plus task-specific train/valid/test node ids and targets. |

### Graph classification

| Family | Names | Optional requirements / caveats |
| --- | --- | --- |
| TU-style graph classification | `mutag`, `imdb-b`, `imdb-m`, `proteins`, `collab`, `nci1`, `nci109`, `ptc-mr`, `enzymes`, `reddit-b`, `reddit-multi-5k`, `reddit-multi-12k` | Optional network/cache. Some graphs lack node attributes; training wrappers may generate degree one-hot features. |
| OGB graph property | `ogbg-molbace`, `ogbg-molhiv`, `ogbg-molpcba`, `ogbg-ppa`, `ogbg-code` | Optional `ogb` dependency plus network/cache. Molecule/code datasets have task-specific labels and can be larger than quick smoke tests. |

### OGB node property and very large benchmarks

| Names | Optional requirements / caveats |
| --- | --- |
| `ogbn-arxiv`, `ogbn-products`, `ogbn-proteins`, `ogbn-papers100M` | Optional `ogb` dependency plus network/cache. Some are large; `ogbn-papers100M` is not a quick validation dataset. `ogbn-proteins` derives node features from edge features and uses ROC-AUC-style evaluation. |

### Recommendation and spatio-temporal datasets

| Family | Names | Optional requirements / caveats |
| --- | --- | --- |
| Recommendation | `yelp2018`, `ali`, `amazon-rec` | Optional network/cache and recommendation-specific layout. Route pipeline/training usage elsewhere. |
| Traffic / spatio-temporal | `pems-stgcn`, `pems-stgat` | Optional network/cache and task-specific tensor formats. Route model/wrapper details elsewhere. |

### OAG-related datasets

| Names | Optional requirements / caveats |
| --- | --- |
| `l0fos`, `aff30`, `arxivvenue` | Optional network/cache and OAG-adjacent data assumptions. OAG-BERT model weights and archive downloads are pipeline/model resources, not ordinary graph dataset loading; route OAG-BERT inference/generation to the pipelines sub-skill. |

## Dependency and backend labels

- **CPU:** Core `Graph`, custom datasets, mask validation, and `DataLoader`
  batching are CPU-capable.
- **CUDA:** Optional acceleration for later model training or sparse operators;
  not required for dataset construction or validation.
- **OGB:** OGB datasets require the optional `ogb` package and may download large
  files.
- **PyG/Jittor/DGL:** Examples or third-party integrations involving these graph
  libraries are optional dependency surfaces and should be routed to the
  models/layers/operators sub-skill; do not require them for this data sub-skill.
- **OAG weights/cache:** OAG-BERT weights and test archives are optional
  network/cache resources and should never be assumed present while choosing a
  graph dataset.

## Safe selection rules

1. If the user needs a quick smoke test, prefer a custom tiny `Graph` over
   `cora` or `mutag` unless cache is already approved.
2. If the user names a built-in dataset, state whether it is likely to download,
   require an optional package, or be large.
3. If the dataset lacks `x`, either choose a model/workflow that does not need
   node features or route the degree-feature decision to the training-wrapper
   sub-skill.
4. If the dataset uses nonstandard fields (`adj`, triples, train dictionaries,
   edge splits, temporal tensors), validate the object shape first and route
   task-specific training/model details out of this sub-skill.
