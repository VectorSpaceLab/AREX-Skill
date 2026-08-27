# RecBole Configuration and Data Reference

This reference is self-contained for future agents preparing RecBole configs,
atomic datasets, and dataset/DataLoader objects.

## 1. `Config` construction and priority

Primary constructor:

```python
from recbole.config import Config

config = Config(
    model=None,
    dataset=None,
    config_file_list=None,
    config_dict=None,
)
```

Use explicit names for ordinary scripts:

```python
config = Config(
    model="BPR",
    dataset="book_clicks",
    config_file_list=["recbole.yaml"],
    config_dict={"load_col": None},
)
```

RecBole merges external settings with this precedence:

1. command line arguments of the form `--parameter_name=value`
2. `config_dict`
3. YAML files in `config_file_list`
4. RecBole default files: overall defaults, model defaults, sample/dataset
   defaults, and model-type quick-start defaults

For `model` and `dataset`, direct constructor arguments are a separate selection
path: if `model="BPR"` or `dataset="book_clicks"` is passed to `Config`, that
constructor value selects the final model/dataset even if external files also
contain `model` or `dataset`. If either constructor argument is `None`, RecBole
looks for that value in the merged external config.

### Priority example for conflicting values

`recbole.yaml`:

```yaml
epochs: 300
use_gpu: true
metrics: [Recall, NDCG]
load_col:
  inter: [user_id, item_id, rating]
```

Python script:

```python
from recbole.config import Config

config = Config(
    model="BPR",
    dataset="book_clicks",
    config_file_list=["recbole.yaml"],
    config_dict={
        "epochs": 50,
        "use_gpu": False,
        "metrics": ["Recall", "MRR"],
        "load_col": {"inter": ["user_id", "item_id", "timestamp"]},
    },
)
print(config["epochs"], config["use_gpu"], config["metrics"], config["load_col"])
```

If the script is launched with shell-safe command-line overrides:

```bash
python run.py --epochs=5 --use_gpu=True \
  --metrics='["Hit"]' \
  --load_col='{"inter":["user_id","item_id"]}'
```

then the resolved values are:

```text
epochs = 5
use_gpu = True
metrics = ["Hit"]
load_col = {"inter": ["user_id", "item_id"]}
```

Without command-line overrides, the `config_dict` values win over YAML:
`epochs=50`, `use_gpu=False`, `metrics=["Recall", "MRR"]`, and the
`timestamp`-based `load_col` dict. YAML wins only over defaults.

Command-line values are parsed from strings and converted when possible. Quote
lists/dicts in the shell so they remain one `--key=value` argument. Arguments
that do not use `--key=value` are not RecBole config keys.

## 2. Config groups and keys

RecBole prints and organizes settings in five practical groups.

### Environment

Common keys:

- `gpu_id`: GPU device id string such as `"0"` or `"0,1"`; an empty string is a
  reliable CPU-only request.
- `use_gpu`: documented boolean GPU preference. Always inspect
  `config["device"]` after construction to see whether RecBole resolved to CPU
  or CUDA.
- `seed`, `reproducibility`, `state`, `show_progress`, `worker`, `encoding`.
- `data_path`: parent directory of the dataset directory for most datasets.
  For dataset `book_clicks`, set `data_path: /path/to/dataset-root` and store
  files in `/path/to/dataset-root/book_clicks/book_clicks.inter`.
- `checkpoint_dir`: directory for checkpoints and default serialized data
  artifacts.
- `save_dataset`, `dataset_save_path`: save or load a filtered `Dataset` object.
  If `dataset_save_path` is null, the default path is under `checkpoint_dir`.
- `save_dataloaders`, `dataloaders_save_path`: save or load split DataLoaders.
  Loading uses `dataloaders_save_path` if set; default loading checks
  `<checkpoint_dir>/<dataset>-for-<model>-dataloader.pth`.

### Data

Common atomic-file and preprocessing keys:

- `field_separator`: delimiter between columns in atomic files; default is tab.
- `seq_separator`: delimiter inside `token_seq` and `float_seq` cells; default
  is a space.
- `USER_ID_FIELD`, `ITEM_ID_FIELD`, `RATING_FIELD`, `TIME_FIELD`.
- `LABEL_FIELD`, `threshold` for point-wise labels from explicit ratings.
- `ITEM_LIST_LENGTH_FIELD`, `LIST_SUFFIX`, `MAX_ITEM_LIST_LENGTH`,
  `POSITION_FIELD` for sequential augmentation.
- `HEAD_ENTITY_ID_FIELD`, `TAIL_ENTITY_ID_FIELD`, `RELATION_ID_FIELD`,
  `ENTITY_ID_FIELD`, `kg_reverse_r`, `entity_kg_num_interval`,
  `relation_kg_num_interval` for knowledge graphs.
- `load_col`, `unload_col`, `unused_col`, `additional_feat_suffix`.
- `rm_dup_inter`, `val_interval`, `filter_inter_by_user_or_item`,
  `user_inter_num_interval`, `item_inter_num_interval`.
- `alias_of_user_id`, `alias_of_item_id`, `alias_of_entity_id`,
  `alias_of_relation_id` for remapping several token fields into one id space.
- `preload_weight`, `normalize_field`, `normalize_all`, `discretization`.
- `benchmark_filename` for pre-split interaction files such as
  `<dataset>.train.inter`, `<dataset>.valid.inter`, and `<dataset>.test.inter`.

### Model

The chosen model affects `MODEL_TYPE`, dataset class selection, defaults, and
which files are useful. Do not deeply explain model architecture here; route
model selection and customization to the sibling model sub-skill.

### Training

Only cover keys that influence config/data setup or routing: `epochs`,
`train_batch_size`, `learner`, `learning_rate`, `train_neg_sample_args`,
`eval_step`, `stopping_step`, `shuffle`, and transform-related fields. Route
training loops and tuning elsewhere.

### Evaluation

`eval_args` is the main data-splitting/evaluation-shape object:

```yaml
eval_args:
  split: {RS: [0.8, 0.1, 0.1]}
  group_by: user
  order: RO
  mode: full
```

Valid shapes:

- `group_by`: `user` or `none`/null depending on task.
- `order`: `RO` for random order, `TO` for temporal order by `TIME_FIELD`.
- `split`: `{RS: [train, valid, test]}` for ratio split or
  `{LS: valid_and_test}` / `{LS: valid_only}` / `{LS: test_only}` for
  leave-one-out split.
- `mode`: string (`full`, `uni100`, `pop100`, `labeled`) or a dict with
  `valid` and `test` keys. A single string is expanded to both phases.

Other evaluation keys commonly visible in data/config answers: `repeatable`,
`metrics`, `topk`, `valid_metric`, `eval_batch_size`, and
`metric_decimal_place`.

## 3. Atomic file suffixes

RecBole identifies input tables by file suffix.

| Suffix | Meaning | Common columns |
| --- | --- | --- |
| `.inter` | user-item interactions | `user_id`, `item_id`, `rating`, `timestamp`, review/context fields |
| `.user` | user features | `user_id`, demographics, profile fields |
| `.item` | item features | `item_id`, category, text/metadata fields |
| `.kg` | knowledge graph triples | `head_id`, `relation_id`, `tail_id` |
| `.link` | item-to-entity links | `item_id`, `entity_id` |
| `.net` | social graph edges | source user, target user, edge features |

Mandatory files by task family:

| Task family | Mandatory atomic files |
| --- | --- |
| General recommendation | `<dataset>.inter` |
| Context-aware recommendation | `<dataset>.inter`, `<dataset>.user`, `<dataset>.item` |
| Knowledge-aware recommendation | `<dataset>.inter`, `<dataset>.kg`, `<dataset>.link` |
| Sequential recommendation | `<dataset>.inter` |
| Social recommendation | `<dataset>.inter`, `<dataset>.net` |

For benchmark/pre-split datasets, `benchmark_filename: [train, valid, test]`
uses files named `<dataset>.train.inter`, `<dataset>.valid.inter`, and
`<dataset>.test.inter` instead of one `<dataset>.inter`.

## 4. Atomic header format

Every atomic file is a table. The first line is the header. Every column header
must have this exact form:

```text
field_name:field_type
```

Supported feature types:

| Type | Meaning | Example |
| --- | --- | --- |
| `token` | single discrete id/category | `user_id:token`, `age:token` |
| `token_seq` | sequence of discrete tokens | `genre:token_seq`, `item_id_list:token_seq` |
| `float` | single continuous value | `rating:float`, `timestamp:float` |
| `float_seq` | sequence of continuous values | `embedding:float_seq` |

Default delimiter is a tab. A minimal general dataset file looks like:

```text
user_id:token	item_id:token	rating:float	timestamp:float
u1	i1	5	1700000000
u1	i2	4	1700000100
```

A common invalid header is:

```text
user_id item_id rating
```

The remediation is to add type suffixes and use the configured delimiter:

```text
user_id:token	item_id:token	rating:float
```

## 5. `load_col`, `unload_col`, extra suffixes, and aliases

### Load all useful columns

```yaml
load_col: null
```

This lets the dataset class load all columns from the files it attempts to
read. It is the simplest setting for initial debugging.

### Load selected interaction columns

```yaml
load_col:
  inter: [user_id, item_id, rating, timestamp]
```

If `load_col` is a dict and a suffix is absent, RecBole treats that source as
not loaded. For context-aware data, include user and item sources explicitly:

```yaml
load_col:
  inter: [user_id, item_id, rating, timestamp]
  user: [user_id, age, gender]
  item: [item_id, category, price]
```

Use `"*"` to load every column from a source while still restricting other
sources:

```yaml
load_col:
  inter: "*"
  item: [item_id, category]
```

### Unload selected columns

Use `unload_col` only when loading broadly and dropping a few fields:

```yaml
load_col: null
unload_col:
  inter: [raw_review_text]
```

Avoid setting both `load_col` and `unload_col` for the same source; it creates
ambiguous guidance and may raise an error when both are non-empty.

### Additional atomic files

To load `<dataset>.ent`:

```yaml
additional_feat_suffix: [ent]
load_col:
  inter: [user_id, item_id, rating, timestamp]
  ent: [ent_id, ent_emb]
```

Additional features are stored on the dataset object with the suffix name, such
as `dataset.ent_feat`. If an extra token should share RecBole's entity id space,
add an alias:

```yaml
alias_of_entity_id: [ent_id]
```

### Alias fields

Aliases are for token-like fields only. Typical uses:

```yaml
alias_of_user_id: [source_user_id, target_user_id]
alias_of_item_id: [also_bought_item_id]
alias_of_entity_id: [head_id, tail_id, linked_entity_id]
alias_of_relation_id: [relation_id]
```

Do not put float fields in an alias list.

## 6. Dataset construction and split DataLoader flow

Build a dataset and split dataloaders with the public RecBole data utilities:

```python
from recbole.config import Config
from recbole.data import (
    create_dataset,
    data_preparation,
    save_split_dataloaders,
    load_split_dataloaders,
)

config = Config(model="BPR", dataset="book_clicks", config_file_list=["recbole.yaml"])
dataset = create_dataset(config)
train_data, valid_data, test_data = data_preparation(config, dataset)
```

`create_dataset(config)` chooses the dataset class from the model type:

general/context/traditional/decision-tree models use the base dataset class;
sequential models use the sequential dataset class; knowledge-aware models use
the knowledge-aware dataset class unless a model-specific dataset class exists.

`data_preparation(config, dataset)` first tries `load_split_dataloaders(config)`.
If no compatible cache is found, it calls `dataset.build()`, creates samplers and
train/valid/test dataloaders, and saves them when `save_dataloaders: true`.

Dataset cache notes:

```yaml
checkpoint_dir: saved
save_dataset: true
dataset_save_path: null
```

- If `dataset_save_path` points to an existing serialized dataset and all data
  arguments plus seed/repeatable are unchanged, `create_dataset` loads it.
- If the saved config no longer matches, RecBole rebuilds from atomic files.
- If `dataset_save_path` is null, RecBole uses a default file under
  `checkpoint_dir`.

Dataloader cache notes:

```yaml
checkpoint_dir: saved
save_dataloaders: true
dataloaders_save_path: null
```

- `load_split_dataloaders` returns cached train/valid/test dataloaders only when
  the saved data arguments, seed, repeatable flag, and `eval_args` match.
- When `dataloaders_save_path` is null, loading checks the default file under
  `checkpoint_dir`.
- If a custom `dataloaders_save_path` is set, point it at an existing compatible
  dataloader pickle. Saving through RecBole's utility uses the default
  checkpoint-based filename.

## 7. Ready-to-adapt YAML snippets

### General recommendation

```yaml
model: BPR
dataset: book_clicks
data_path: /path/to/dataset-root
load_col:
  inter: [user_id, item_id, rating, timestamp]

field_separator: "\t"
seq_separator: " "
eval_args:
  split: {RS: [0.8, 0.1, 0.1]}
  group_by: user
  order: RO
  mode: full
metrics: [Recall, MRR, NDCG, Hit, Precision]
topk: [10]
valid_metric: MRR@10
```

Expected file: `/path/to/dataset-root/book_clicks/book_clicks.inter`.

### Sequential recommendation

```yaml
model: SASRec
dataset: sessions
data_path: /path/to/dataset-root
load_col:
  inter: [user_id, item_id, timestamp]

MAX_ITEM_LIST_LENGTH: 50
ITEM_LIST_LENGTH_FIELD: item_length
LIST_SUFFIX: _list
POSITION_FIELD: position_id
repeatable: true
eval_args:
  split: {LS: valid_and_test}
  group_by: user
  order: TO
  mode: full
train_neg_sample_args: null
```

Expected file: `/path/to/dataset-root/sessions/sessions.inter` with a timestamp
field if `order: TO` is used.

### Context-aware recommendation

```yaml
model: FM
dataset: ad_clicks
data_path: /path/to/dataset-root
load_col:
  inter: [user_id, item_id, label, timestamp]
  user: [user_id, age, country]
  item: [item_id, category, price]

LABEL_FIELD: label
eval_args:
  split: {RS: [0.8, 0.1, 0.1]}
  group_by: null
  order: RO
  mode: labeled
metrics: [AUC, LogLoss]
valid_metric: AUC
train_neg_sample_args: null
```

Expected files: `ad_clicks.inter`, `ad_clicks.user`, and `ad_clicks.item`.

### Knowledge-aware recommendation

```yaml
model: KGAT
dataset: movie_kg
data_path: /path/to/dataset-root
load_col:
  inter: [user_id, item_id, rating, timestamp]
  kg: [head_id, relation_id, tail_id]
  link: [item_id, entity_id]

HEAD_ENTITY_ID_FIELD: head_id
TAIL_ENTITY_ID_FIELD: tail_id
RELATION_ID_FIELD: relation_id
ENTITY_ID_FIELD: entity_id
kg_reverse_r: false
entity_kg_num_interval: "[0,inf)"
relation_kg_num_interval: "[0,inf)"
```

Expected files: `movie_kg.inter`, `movie_kg.kg`, and `movie_kg.link`.
