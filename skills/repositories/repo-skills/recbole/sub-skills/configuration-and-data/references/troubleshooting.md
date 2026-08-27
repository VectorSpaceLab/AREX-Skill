# RecBole Configuration and Data Troubleshooting

Use this table when a RecBole run fails before or during dataset/DataLoader
preparation. First inspect resolved config values, because external config
priority often differs from what the user remembers editing.

## Fast triage checklist

```python
print("dataset =", config["dataset"])
print("data_path =", config["data_path"])
print("load_col =", config["load_col"])
print("unload_col =", config["unload_col"])
print("eval_args =", config["eval_args"])
print("metrics =", config["metrics"])
print("device =", config["device"])
```

Then validate atomic files without importing RecBole:

```bash
python scripts/validate_atomic_dataset.py /path/to/dataset-root/my_dataset \
  --dataset my_dataset --task-family general
```

Add `--config-yaml recbole.yaml` to check `load_col` against headers when
PyYAML is available.

## Symptoms, causes, and fixes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `File ... not exist` for `<dataset>.inter` | `data_path` points at the dataset directory instead of its parent, or the file name does not start with the dataset name. | For `dataset: my_dataset`, put files under `/path/to/dataset-root/my_dataset/` and set `data_path: /path/to/dataset-root`. The interaction file should be `my_dataset.inter` unless using `benchmark_filename`. |
| RecBole says the dataset directory is missing or tries to download data | The expected local directory does not exist, or `dataset` is misspelled. | Create `/path/to/dataset-root/<dataset>/` with correctly named atomic files, or correct `dataset`/`data_path`. |
| Header parsing fails with too few values, too many values, or unsupported type | Header columns are not `field_name:field_type`, or an unsupported type was used. | Rewrite the first line with exactly one colon per column and one of `token`, `token_seq`, `float`, `float_seq`. Example: `user_id:token<TAB>item_id:token<TAB>rating:float`. |
| Tiny `.inter` has header `user_id item_id rating` | Space-separated names without RecBole type suffixes; default delimiter is tab. | Replace the header with `user_id:token\titem_id:token\trating:float` and keep data rows tab-delimited, or set `field_separator` and use matching delimiters consistently. |
| `.user` or `.item` file exists but features are ignored | `load_col` is a dict and does not contain `user` or `item`; RecBole loads no columns for omitted suffixes. | Add each source explicitly, e.g. `load_col: {inter: [user_id,item_id], user: [user_id,age], item: [item_id,category]}`, or set `load_col: null` while debugging. |
| `No columns has been loaded from [inter]` | `load_col.inter` names do not match header field names after removing type suffixes. | Compare `load_col` names to the header fields. Use `scripts/validate_atomic_dataset.py ... --config-yaml recbole.yaml` to catch mismatches. |
| `load_col` and `unload_col` conflict | Both settings were supplied for the same non-empty source. | Prefer one strategy: either use `load_col` to list what to keep, or `load_col: null` plus `unload_col` to drop a small set. |
| Additional file `<dataset>.ent` not found | `additional_feat_suffix: [ent]` is set but the file is missing or named with the wrong dataset prefix. | Create `/path/to/dataset-root/<dataset>/<dataset>.ent`, or remove `ent` from `additional_feat_suffix`. |
| Extra suffix is present but not loaded | The suffix was not listed in `additional_feat_suffix`, or its fields were omitted from `load_col`. | Add both `additional_feat_suffix: [suffix]` and `load_col: {suffix: [...]}`. |
| Alias error says a field is non-token-like | `alias_of_user_id`, `alias_of_item_id`, `alias_of_entity_id`, or `alias_of_relation_id` contains a `float`/`float_seq` field or a missing field. | Alias only `token`/`token_seq` id fields that are loaded by `load_col`. |
| Context-aware model cannot find labels or uses wrong evaluation mode | Context-aware defaults often use labeled/value metrics, but custom config may override `LABEL_FIELD`, `threshold`, `eval_args.mode`, or metrics. | Ensure the label/rating field is loaded. For explicit labeled evaluation, use `mode: labeled`, value metrics such as `AUC`/`LogLoss`, and `train_neg_sample_args: null`. Route metric strategy to the training/evaluation sub-skill if needed. |
| Sequential model complains about repeatable recommendation | Sequential configs require repeatable evaluation. | Set `repeatable: true`; use `eval_args` with leave-one-out and temporal order when appropriate: `split: {LS: valid_and_test}`, `order: TO`. |
| Temporal split/order fails or behaves unexpectedly | `eval_args.order: TO` is used but `TIME_FIELD` is not present or not loaded. | Add a timestamp column such as `timestamp:float`, include it in `load_col.inter`, and ensure `TIME_FIELD: timestamp`. |
| Knowledge-aware model fails on KG/link fields | `.kg` or `.link` file missing, header names differ from configured `HEAD_ENTITY_ID_FIELD`, `RELATION_ID_FIELD`, `TAIL_ENTITY_ID_FIELD`, or `ENTITY_ID_FIELD`, or `load_col` omits required fields. | Provide `<dataset>.kg` and `<dataset>.link`; align headers and config fields; include `kg: [head_id, relation_id, tail_id]` and `link: [item_id, entity_id]` in `load_col`. |
| Benchmark/pre-split files are not found | `benchmark_filename` expects `<dataset>.<name>.inter`, not arbitrary filenames. | For `benchmark_filename: [train, valid, test]`, create `<dataset>.train.inter`, `<dataset>.valid.inter`, and `<dataset>.test.inter`. |
| YAML parser or RecBole sees list/dict as a string | Bad YAML indentation/quoting or shell quotes stripped a CLI value. | In YAML, use block lists/dicts or bracket syntax. In CLI, quote the whole value: `--metrics='["Recall","NDCG"]'` and `--eval_args='{"split":{"RS":[0.8,0.1,0.1]},"mode":"full"}'`. |
| A config value seems ignored | Higher-priority source overrides it: command line > `config_dict` > YAML files > defaults. Direct `model`/`dataset` constructor args also select those values. | Print the resolved config and remove or update the higher-priority value. Check launch scripts for hidden `--key=value` overrides. |
| `metrics` unexpectedly becomes a one-element list | A string metric is normalized to a list internally. | This is normal: `metrics: Recall` becomes `config["metrics"] == ["Recall"]`. Use YAML list syntax for multiple metrics. |
| Ranking and value metrics cannot be mixed | RecBole checks metric types and rejects mixed ranking/value metrics. | Choose one family: ranking (`Recall`, `MRR`, `NDCG`, `Hit`, `Precision`, etc.) or value (`AUC`, `MAE`, `RMSE`, `LogLoss`). Route metric design to the training/evaluation sub-skill. |
| `topk` type error | `topk` is not an int or list of positive ints. | Use `topk: [10]`, `topk: [5, 10, 20]`, or CLI `--topk='[10]'`. |
| GPU was requested but RecBole uses CPU | CUDA is unavailable, `gpu_id` is empty, or the environment cannot see the requested GPU. | Inspect `config["device"]`. For CPU, set `gpu_id: ""` and optionally `use_gpu: false`. For GPU, ensure CUDA is available before blaming RecBole config; `use_gpu` alone is not proof that CUDA was selected. |
| Saved filtered dataset is ignored | The serialized dataset exists but its stored data arguments, seed, or repeatable flag differ from the current config. | Reuse exactly the same data config or delete/rebuild the cache. Set `save_dataset: true` and `dataset_save_path` deliberately if sharing a cache. |
| Saved dataloaders are ignored | Cache path missing or stored config differs in data arguments, seed, repeatable, or `eval_args`. | Keep `eval_args` identical, or rebuild. If using a custom `dataloaders_save_path`, point it to an existing compatible pickle. |
| `load_col` works in YAML but not CLI | Shell parsing stripped braces, spaces, or quotes. | Prefer YAML for complex `load_col`. If CLI is necessary, use single quotes around JSON/Python-literal syntax: `--load_col='{"inter":["user_id","item_id"]}'`. |

## Exact remediation for invalid tiny `.inter` headers

Bad file:

```text
user_id item_id rating
u1 i1 5
u1 i2 4
```

Problems:

1. Header has no `:type` suffixes.
2. Default RecBole delimiter is tab, not a space.
3. `rating` should be typed as `float`; ids should be `token`.

Fixed tab-delimited file:

```text
user_id:token	item_id:token	rating:float
u1	i1	5
u1	i2	4
```

Matching minimal YAML:

```yaml
dataset: tiny
data_path: /path/to/dataset-root
field_separator: "\t"
load_col:
  inter: [user_id, item_id, rating]
```

Place it at `/path/to/dataset-root/tiny/tiny.inter`.

## Resolving YAML/dict/CLI override conflicts

Given:

```yaml
# recbole.yaml
epochs: 300
use_gpu: true
metrics: [Recall, NDCG]
load_col:
  inter: [user_id, item_id, rating]
```

and:

```python
config = Config(
    model="BPR",
    dataset="tiny",
    config_file_list=["recbole.yaml"],
    config_dict={
        "epochs": 50,
        "use_gpu": False,
        "metrics": ["Recall", "MRR"],
        "load_col": {"inter": ["user_id", "item_id", "timestamp"]},
    },
)
```

Without command-line overrides, the dict wins:

```text
epochs=50
use_gpu=False
metrics=["Recall", "MRR"]
load_col={"inter": ["user_id", "item_id", "timestamp"]}
```

With this launch:

```bash
python run.py --epochs=5 --use_gpu=True \
  --metrics='["Hit"]' \
  --load_col='{"inter":["user_id","item_id"]}'
```

command line wins:

```text
epochs=5
use_gpu=True
metrics=["Hit"]
load_col={"inter": ["user_id", "item_id"]}
```

If the final `load_col` omits `rating` or `timestamp`, those columns are not
loaded even if the YAML listed them. Diagnose by printing `config["load_col"]`,
not by rereading only the YAML file.
