# SPLADE Hydra Configuration

SPLADE's classic entry points import `CONFIG_NAME` and `CONFIG_PATH` from `conf.CONFIG_CHOICE`. That module chooses the Hydra config before the entry point runs.

## Config Source Selection

Use exactly one of these environment variables:

| Variable | Use when | Example |
| --- | --- | --- |
| `SPLADE_CONFIG_NAME` | Selecting a config from the installed package `conf/` tree | `SPLADE_CONFIG_NAME=config_default.yaml` |
| `SPLADE_CONFIG_FULLPATH` | Reusing a composed config saved by a previous run | `SPLADE_CONFIG_FULLPATH=experiments/run/checkpoint/config.yaml` |

If neither variable is set, SPLADE defaults to `config_default`. If the selected name contains `.yaml`, the code strips that suffix, so `config_default` and `config_default.yaml` are equivalent as environment values.

Do not set both variables. SPLADE asserts that the number of set config-source variables is at most one.

## Default Config Composition

The default config composes these groups:

| Group | Default option | Purpose |
| --- | --- | --- |
| `train/config` | `splade_toy` | Training hyperparameters for a tiny toy run |
| `train/data` | `toy` | Toy training triples and validation data |
| `train/model` | `splade` | SPLADE model initialization defaults |
| `index` | `toy` | Toy document collection path |
| `retrieve_evaluate` | `toy` | Toy query/qrel/evaluation settings |
| `flops` | `toy` | Toy query collection for FLOPS estimation |

The same groups can be overridden on the command line, for example:

```bash
python -m splade.index index=msmarco
python -m splade.retrieve retrieve_evaluate=msmarco config.top_k=1000
python -m splade.train train/data=msmarco train/model=splade init_dict.model_type_or_dir=bert-base-uncased
```

## Parameter Overrides vs Group Overrides

Hydra has two different naming systems:

- Override a config group with its config path, such as `train/data=msmarco`, `train/model=splade_cocondenser`, `index=toy`, or `retrieve_evaluate=msmarco`.
- Override a parameter with its package position in the composed config, such as `config.checkpoint_dir=...`, `config.index_dir=...`, `config.out_dir=...`, `init_dict.model_type_or_dir=...`, or `config.regularizer.FLOPS.lambda_q=0.06`.

If a YAML file contains `# @package config`, values from that file appear under the `config.` namespace. If it contains `# @package _global_`, its values are placed at the root of the composed config.

## Required Output Directories

`conf/config_default.yaml` leaves these as unresolved `???` values:

```yaml
config:
  checkpoint_dir: ???
  index_dir: ???
  out_dir: ???
```

Always fill them when using the default/toy workflow:

```bash
config.checkpoint_dir=experiments/toy/checkpoint \
config.index_dir=experiments/toy/index \
config.out_dir=experiments/toy/out
```

A richer config may already specify output directories, but overriding them is still safer because full configurations can target large or conventional locations such as `models/...`.

## Post-Training Config Contract

Classic SPLADE commands use a saved training config as the contract between steps:

1. `splade.train` creates `config.checkpoint_dir` and saves the composed config as `config.checkpoint_dir/config.yaml`.
2. `splade.index`, `splade.retrieve`, `splade.flops`, and `splade.create_anserini` call initialization logic that loads `config.checkpoint_dir/config.yaml` to recover model settings.
3. If no checkpoint config exists because you are using a Hugging Face model directly, set `config.pretrained_no_yamlconfig=true` and provide `init_dict.model_type_or_dir=<model-id-or-dir>`.

When using a split workflow, keep `config.checkpoint_dir` consistent across train, index, retrieve, FLOPS, and export commands unless you intentionally switch checkpoints.

## Key Config Fields

| Field | Meaning | Notes |
| --- | --- | --- |
| `config.checkpoint_dir` | Training output and checkpoint config location | Required for `train`; normally read by later steps |
| `config.index_dir` | Sparse index or export output location | Required for index/retrieve/export workflows |
| `config.out_dir` | Retrieval/evaluation/FLOPS output location | Required for retrieve/evaluate/FLOPS workflows |
| `config.pretrained_no_yamlconfig` | Skip loading `checkpoint_dir/config.yaml` | Use for direct Hugging Face model evaluation |
| `init_dict.model_type_or_dir` | Model id or local model directory | Set to a Hugging Face model id for pretrained workflows |
| `init_dict.model_type_or_dir_q` | Optional query encoder model id/directory | Used by two-tower/efficient variants |
| `config.index_retrieve_batch_size` | Batch size for indexing/export/FLOPS query encoding | Lower for CPU/small GPU runs |
| `config.top_k` | Number of retrieved documents per query | Usually from `retrieve_evaluate` config |
| `config.threshold` | Retrieval score threshold | Usually from `retrieve_evaluate` config |
| `config.eval_metric` | Metrics passed to evaluation | Example toy value: `[[mrr_10, recall]]` |
| `config.retrieval_name` | Dataset output names | Output run paths use these names |
| `data.COLLECTION_PATH` | Document collection path | Comes from `index=<option>` group |
| `data.Q_COLLECTION_PATH` | Query collection path list | Comes from `retrieve_evaluate=<option>` group |
| `data.EVAL_QREL_PATH` | Qrel path list | `None` entries skip metric computation |
| `data.flops_queries` | Query collection for FLOPS estimate | Comes from `flops=<option>` group |

## Quantization Overrides for `create_anserini`

`splade.create_anserini` expects additional Hydra keys for quantization. Because these keys are not always present in the base config, add them with Hydra's `+` syntax:

```bash
+quantization_factor_document=100 +quantization_factor_query=100
```

Use integers such as `100` as starting values. Export/pruning/evaluation trade-offs and downstream engine setup are handled by `../pruning-export-evaluation/SKILL.md`.

## Help Checks

Hydra help is safe for entry points whose imports are satisfied:

```bash
python -m splade.index --help
python -m splade.create_anserini --help
python -m splade.hf_train --help
```

`python -m splade.retrieve --help` and `python -m splade.evaluate --help` can fail before showing help if `pytrec_eval` is not installed, because evaluation modules import it at import time.
