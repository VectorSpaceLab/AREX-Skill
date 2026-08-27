# Configuration

FlashRAG centralizes experiment settings in `Config`. Agents should treat configuration as a merge of defaults, YAML, and Python overrides, then validate paths and data before expensive retrieval or generation work.

## Merge priority

Effective values are resolved in this order, highest priority first:

1. `config_dict` passed to `Config(..., config_dict=...)`.
2. YAML file passed as `config_file_path`.
3. FlashRAG default settings from `basic_config.yaml`.

Nested dictionaries are shallow-merged at the section level. For example, a YAML `model2path` map can override only selected aliases while keeping default aliases; a later `config_dict` `model2path` entry can override selected YAML aliases.

## High-impact `basic_config` sections

| Section | Common keys | Why agents should inspect it |
| --- | --- | --- |
| Global paths | `model2path`, `model2pooling`, `method2index` | Alias maps drive automatic model, pooling, and index path resolution. |
| Environment | `data_dir`, `save_dir`, `gpu_id`, `dataset_name`, `split`, `test_sample_num`, `random_sample`, `seed`, `save_intermediate_data`, `save_note` | Controls data location, reproducibility, sampling, GPU visibility, and output side effects. |
| Retrieval | `retrieval_method`, `retrieval_model_path`, `index_path`, `corpus_path`, `retrieval_topk`, cache keys, reranker keys | Must be consistent with corpus/index preparation; hand off to `retrieval-and-indexing` for build/search details. |
| Generator | `framework`, `generator_model`, `generator_model_path`, `generator_max_input_len`, `generator_batch_size`, `generation_params`, `openai_setting` | Needed before pipeline execution; hand off to `pipelines-and-methods` for runtime method details. |
| Evaluation | `metrics`, `metric_setting`, `save_metric_score` | Relevant after outputs are produced; metrics/WebUI are outside this sub-skill. |

## Required and derived keys

`Config` expects defaults or user inputs to provide at least these root keys: `split`, `gpu_id`, `dataset_name`, `data_dir`, `model2path`, `model2pooling`, `method2index`, `retrieval_method`, `index_path`, `generator_model`, `metric_setting`, `seed`, `save_note`, and `save_dir` unless `disable_save` is used for dry inspection.

Important derived behavior:

- `split: null` becomes `['train', 'dev', 'test']`.
- `split: test` becomes `['test']`; a list stays a list.
- `dataset_path` is derived as `data_dir` joined with `dataset_name`.
- `retrieval_model_path` defaults from `model2path[retrieval_method]` or the method string itself.
- `retrieval_pooling_method` defaults from `model2pooling` by substring match, otherwise `mean`.
- `index_path` can default from `method2index[retrieval_method]`; if no mapping exists, FlashRAG prints `Index is empty!!`.
- `generator_model_path` defaults from `model2path[generator_model]` or the generator model string itself.
- `metric_setting.tokenizer_name` may be remapped through `model2path` when it is not a known OpenAI tokenizer alias.

## Save and output side effects

By default, constructing `Config` creates a timestamped run directory under `save_dir` and writes the effective `config.yaml` there. The directory name includes `dataset_name`, a minute-level timestamp, and `save_note`.

For validation, unit tests, or priority checks where no directories should be created, set:

```yaml
disable_save: true
```

or pass `{'disable_save': True}` in `config_dict`. This suppresses `_prepare_dir`, but `Config` still imports runtime dependencies for device and seed setup.

## Reproducibility checklist

- Set `seed` explicitly; non-integer seed values fall back to `2025` during runtime setup.
- Set `random_sample: false` when comparing exact expected examples.
- Set `test_sample_num` only for intentional test/dev sampling.
- Use stable relative project paths in reusable examples; avoid embedding machine-specific absolute paths.
- Review `save_dir`, `save_note`, and `disable_save` before constructing `Config` in tests or dry runs.
- Keep corpus/index paths aligned with the retrieval method; route to `retrieval-and-indexing` when index creation or search behavior is involved.

## Minimal dry-inspection config

```yaml
disable_save: true
dataset_name: nq
data_dir: dataset
split: test
retrieval_method: e5
corpus_path: indexes/general_knowledge.jsonl
index_path: null
generator_model: llama3-8B-instruct
framework: vllm
save_dir: output
save_note: dry-run
seed: 2024
```

This is enough to check shape and priority expectations, but actual FlashRAG runtime may still need optional packages such as PyYAML, NumPy, Torch, datasets, model backends, or retrieval dependencies depending on the module imported.
