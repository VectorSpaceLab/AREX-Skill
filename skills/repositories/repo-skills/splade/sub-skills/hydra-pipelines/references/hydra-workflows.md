# Hydra Workflow Commands

This reference covers the classic SPLADE module entry points powered by Hydra. Commands shown here are templates: replace placeholder paths with real project paths before running them.

## Module Map

| Entry point | Main job | Required runtime inputs | Main outputs |
| --- | --- | --- | --- |
| `python -m splade.all` | Run train, index, retrieve/evaluate, FLOPS, and index-figure sequence | Config, training data, collection/query/qrel data, output dirs | Checkpoint, sparse index, run/eval outputs, FLOPS |
| `python -m splade.train` | Train a classic SPLADE model | Config, training pairs/triplets, `config.checkpoint_dir` | `config.checkpoint_dir/config.yaml`, checkpoints |
| `python -m splade.index` | Build a SPLADE inverted index | Checkpoint config or pretrained override, collection path, `config.index_dir` | Sparse index files and stats |
| `python -m splade.retrieve` | Encode queries, retrieve from index, evaluate | Checkpoint config or pretrained override, query/qrel paths, `config.index_dir`, `config.out_dir` | Per-dataset `run.json`, `perf.json`, aggregate metrics |
| `python -m splade.evaluate` | Evaluate existing run files | Qrels, retrieval names, `config.out_dir` with runs | `perf.json`, `perf_all_datasets.json` |
| `python -m splade.flops` | Estimate query/document FLOPS from saved index | Checkpoint config, index, flops query collection, `config.out_dir` | `flops.json` |
| `python -m splade.create_anserini` | Export document/query vectors for Anserini | Checkpoint/pretrained config, collection/query data, quantization factors | `docs_anserini.jsonl`, `queries_anserini.tsv` under the index/output area |

## Toy All-in-One Workflow

Use this only for a tiny sanity workflow. It still trains a model, so expect model initialization and local compute.

```bash
export SPLADE_CONFIG_NAME=config_default.yaml
python -m splade.all \
  config.checkpoint_dir=experiments/toy/checkpoint \
  config.index_dir=experiments/toy/index \
  config.out_dir=experiments/toy/out
```

Why those overrides are required: the default config declares `config.checkpoint_dir`, `config.index_dir`, and `config.out_dir` as unresolved Hydra values (`???`). Without replacements, Hydra/OmegaConf fails before or during the run.

## Split Train, Index, Retrieve, Evaluate Flow

A safer production pattern is to split long-running steps:

```bash
export SPLADE_CONFIG_NAME=config_default.yaml
python -m splade.train \
  config.checkpoint_dir=experiments/toy/checkpoint \
  config.index_dir=experiments/toy/index \
  config.out_dir=experiments/toy/out

python -m splade.index \
  config.checkpoint_dir=experiments/toy/checkpoint \
  config.index_dir=experiments/toy/index

python -m splade.retrieve \
  config.checkpoint_dir=experiments/toy/checkpoint \
  config.index_dir=experiments/toy/index \
  config.out_dir=experiments/toy/out

python -m splade.evaluate \
  config.out_dir=experiments/toy/out
```

`train` writes the composed training configuration to `config.checkpoint_dir/config.yaml`. Later commands use that saved file to recover training-time model settings unless `config.pretrained_no_yamlconfig=true` is set.

## Full Config Selection

Use one of the richer bundled config names for full MS MARCO-style runs. These configs often provide default `checkpoint_dir`, `index_dir`, and `out_dir`, but still inspect/override them so large outputs do not land in an unexpected location.

```bash
export SPLADE_CONFIG_NAME=config_splade++_cocondenser_ensembledistil.yaml
python -m splade.train \
  config.checkpoint_dir=experiments/cocondenser/checkpoint \
  config.index_dir=experiments/cocondenser/index \
  config.out_dir=experiments/cocondenser/out
```

For smaller hardware, prefer the mono-GPU config as a starting point and reduce batch sizes further if needed:

```bash
export SPLADE_CONFIG_NAME=config_splade++_cocondenser_ensembledistil_monogpu.yaml
python -m splade.train \
  config.train_batch_size=4 \
  config.eval_batch_size=4 \
  config.index_retrieve_batch_size=4 \
  config.checkpoint_dir=experiments/monogpu/checkpoint \
  config.index_dir=experiments/monogpu/index \
  config.out_dir=experiments/monogpu/out
```

## Pretrained Hugging Face Evaluation

When evaluating an already published Hugging Face model and no SPLADE checkpoint config exists, set `config.pretrained_no_yamlconfig=true`.

```bash
export SPLADE_CONFIG_NAME=config_splade++_cocondenser_ensembledistil.yaml
python -m splade.index \
  init_dict.model_type_or_dir=naver/splade-cocondenser-ensembledistil \
  config.pretrained_no_yamlconfig=true \
  config.index_dir=experiments/pretrained/index

python -m splade.retrieve \
  init_dict.model_type_or_dir=naver/splade-cocondenser-ensembledistil \
  config.pretrained_no_yamlconfig=true \
  config.index_dir=experiments/pretrained/index \
  config.out_dir=experiments/pretrained/out
```

Change the retrieval dataset by overriding a config group, for example `retrieve_evaluate=msmarco` or `retrieve_evaluate=toy`. Change specific values with parameter overrides, for example `config.top_k=1000` or `config.threshold=0`.

## Saved Experiment Config Flow

Use `SPLADE_CONFIG_FULLPATH` when a prior checkpoint directory already contains the composed config you want to reuse:

```bash
export SPLADE_CONFIG_FULLPATH=experiments/toy/checkpoint/config.yaml
python -m splade.index \
  config.index_dir=experiments/toy/index

python -m splade.retrieve \
  config.index_dir=experiments/toy/index \
  config.out_dir=experiments/toy/out
```

Do not set `SPLADE_CONFIG_NAME` and `SPLADE_CONFIG_FULLPATH` together; SPLADE asserts that at most one is present.

## Anserini Export Handoff

`python -m splade.create_anserini` creates Anserini-readable document/query files. This sub-skill covers only the SPLADE command shape; downstream Anserini, pruning, PISA, and BEIR details belong to `../pruning-export-evaluation/SKILL.md`.

```bash
export SPLADE_CONFIG_FULLPATH=experiments/toy/checkpoint/config.yaml
python -m splade.create_anserini \
  config.index_dir=experiments/toy/anserini-export \
  +quantization_factor_document=100 \
  +quantization_factor_query=100
```

For a pretrained Hugging Face model:

```bash
export SPLADE_CONFIG_NAME=config_splade++_cocondenser_ensembledistil.yaml
python -m splade.create_anserini \
  init_dict.model_type_or_dir=naver/splade-cocondenser-ensembledistil \
  config.pretrained_no_yamlconfig=true \
  config.index_dir=experiments/pretrained/anserini-export \
  +quantization_factor_document=100 \
  +quantization_factor_query=100
```

## Safe Command Builder

Use the bundled helper to generate commands without running them:

```bash
python sub-skills/hydra-pipelines/scripts/splade_hydra_command_builder.py toy-all \
  --checkpoint-dir experiments/toy/checkpoint \
  --index-dir experiments/toy/index \
  --out-dir experiments/toy/out
```

The helper emits shell commands and validates common omissions such as missing checkpoint/index/output directories and mutually exclusive config source options.
