# Hydra Pipeline Troubleshooting

## `Missing mandatory value: config.checkpoint_dir`, `config.index_dir`, or `config.out_dir`

Cause: the selected config contains Hydra/OmegaConf `???` placeholders. The default toy config intentionally leaves output directories unresolved.

Fix: pass all relevant output overrides for the entry point:

```bash
config.checkpoint_dir=experiments/run/checkpoint \
config.index_dir=experiments/run/index \
config.out_dir=experiments/run/out
```

For split workflows, `train` needs `config.checkpoint_dir`; `index` needs `config.checkpoint_dir` and `config.index_dir`; `retrieve` needs `config.checkpoint_dir`, `config.index_dir`, and `config.out_dir`.

## `SPLADE_CONFIG_NAME` vs `SPLADE_CONFIG_FULLPATH`

Symptoms:

- Assertion failure before Hydra starts.
- Wrong config loaded despite command-line overrides.
- Saved checkpoint config is ignored.

Rules:

- Set `SPLADE_CONFIG_NAME` for bundled configs such as `config_default.yaml`, `config_splade++_selfdistil.yaml`, or `config_splade++_cocondenser_ensembledistil.yaml`.
- Set `SPLADE_CONFIG_FULLPATH` for a saved `config.yaml` from a checkpoint directory.
- Never set both at the same time.
- If neither is set, SPLADE uses `config_default`.

## `Cannot find primary config` or config option not found

Cause: the config name/group does not exist in the installed SPLADE `conf/` tree, or a full path points to a missing file.

Fix:

- Use a known config file name from the SPLADE config tree, with or without `.yaml`.
- Use group overrides with available options, for example `index=toy`, `index=msmarco`, `retrieve_evaluate=toy`, or `retrieve_evaluate=msmarco`.
- For a saved config, point `SPLADE_CONFIG_FULLPATH` to the actual `config.yaml` written by `splade.train`.

## Package Override vs Parameter Override Confusion

Symptoms:

- Hydra says an override key is invalid.
- A parameter override silently goes under the wrong namespace.
- A group override is written as though it were a parameter.

Use these patterns:

```bash
# Config group override: choose another YAML option from a group.
train/data=msmarco
retrieve_evaluate=msmarco

# Parameter override: use the composed config namespace.
init_dict.model_type_or_dir=naver/splade-cocondenser-ensembledistil
config.top_k=1000
config.regularizer.FLOPS.lambda_q=0.06
```

If a config file uses `# @package config`, its fields are under `config.`. If it uses `# @package _global_`, its fields are at the root.

## `version_base` Hydra Error or Warning

Symptoms:

- `TypeError: main() got an unexpected keyword argument 'version_base'`.
- Warnings that `version_base` is not specified for some older entry points.
- OmegaConf/Hydra dependency pin conflicts.

Cause: current SPLADE source includes several `@hydra.main(..., version_base="1.2")` entry points, while historical package metadata pins older OmegaConf/Hydra-era dependencies. Old Hydra releases do not understand `version_base`; newer Hydra may warn about older decorators and missing `_self_` in defaults.

Fix:

- Use a Hydra version that supports `version_base`, such as the Hydra 1.2 family, with a compatible OmegaConf release.
- Treat metadata pin warnings as dependency-drift signals; verify with safe help commands such as `python -m splade.index --help`.
- Do not fix this by editing SPLADE runtime commands; solve it in the environment.

## `ModuleNotFoundError: No module named 'pytrec_eval'`

Cause: `splade.retrieve`, `splade.evaluate`, and reranking paths import evaluation code that imports `pytrec_eval` at module import time. Help can fail before Hydra displays usage.

Fix:

- Install `pytrec_eval`/`pytrec-eval` in an environment with the compiler/network access needed by the package build.
- If only indexing/exporting, use `python -m splade.index` or `python -m splade.create_anserini` without importing retrieve/evaluate paths.
- If metrics are not needed, still expect `splade.retrieve` to import evaluation modules; plan the dependency rather than assuming retrieval-only help is dependency-free.

## Missing `checkpoint_dir/config.yaml`

Symptoms:

- Index/retrieve/export fails while loading `config.checkpoint_dir/config.yaml`.
- A pretrained Hugging Face model command still tries to read a checkpoint config.

Fix:

- If you trained with `splade.train`, reuse the same `config.checkpoint_dir` and confirm the saved config exists.
- If you are using a model id or local model directory directly, add `config.pretrained_no_yamlconfig=true` and set `init_dict.model_type_or_dir=...`.
- For a saved experiment, consider `SPLADE_CONFIG_FULLPATH=<checkpoint-dir>/config.yaml` to make the intended composed config explicit.

## CPU vs GPU Expectations

Classic SPLADE commands can import and show help on CPU, and toy commands may run slowly on CPU. Real training and full indexing/retrieval are GPU-oriented and can be memory intensive.

Practical mitigations:

- Start with toy configs for command validation.
- Use mono-GPU configs for smaller hardware.
- Lower `config.train_batch_size`, `config.eval_batch_size`, and `config.index_retrieve_batch_size` when memory is limited.
- Expect Hugging Face model downloads unless the model cache is already populated or a local model directory is used.

## Model Download or Offline Errors

Symptoms:

- Hugging Face model id cannot be resolved.
- Tokenizer/model files are missing in an offline environment.
- TLS/network failures occur during dependency or model acquisition.

Fix:

- Use a local model directory in `init_dict.model_type_or_dir` if offline.
- Pre-populate the Hugging Face cache before running SPLADE commands.
- For two-encoder variants, also set `init_dict.model_type_or_dir_q` when the query encoder is separate.

## `create_anserini` Quantization Key Errors

Cause: quantization factors are accessed as root Hydra keys by `splade.create_anserini`.

Fix: pass them with `+` so Hydra creates the keys when absent:

```bash
+quantization_factor_document=100 +quantization_factor_query=100
```

If export succeeds, hand off downstream indexing/search/evaluation/pruning setup to `../pruning-export-evaluation/SKILL.md`.
