# API Reference

This reference summarizes the FlashRAG config and dataset APIs relevant to input preparation. It is not a pipeline execution guide.

## `flashrag.config.Config`

| Operation | Behavior | Agent note |
| --- | --- | --- |
| `Config(config_file_path=None, config_dict={})` | Loads YAML config, merges dict overrides, merges defaults, validates/normalizes, initializes device/seed, and prepares output directory unless disabled. | Use `disable_save: true` for dry checks. Runtime construction imports PyYAML and later Torch/NumPy. |
| `_load_file_config(path)` | Loads YAML with a custom `yaml.FullLoader` float resolver. | YAML syntax errors surface before FlashRAG-specific checks. |
| `_update_dict(old, new)` | Updates top-level keys; if a new value is a dict and the key already exists, it merges that nested dict into the existing one. | This is a shallow section merge, not a recursive deep merge. |
| `_check_final_config()` | Normalizes `split`: `None` to `['train','dev','test']`, string to one-item list. | Missing `split` causes a key error before normalization. |
| `_set_additional_key()` | Derives `dataset_path`, retrieval model/index/pooling paths, reranker paths, generator path, and metric tokenizer path. | Missing required maps or model keys can fail early. |
| `_init_device()` | Sets `CUDA_VISIBLE_DEVICES` from `gpu_id`, imports Torch if available, and records `gpu_num`/`device`. | Missing Torch may be tolerated for GPU counting, but seed setup later imports Torch directly. |
| `_set_seed()` | Converts `seed` to int, seeds Python, NumPy, and Torch, and sets deterministic CUDNN flags. | Missing NumPy or Torch breaks real `Config` construction. |
| `_prepare_dir()` | Creates timestamped `save_dir` and writes effective `config.yaml`. | Suppress with `disable_save: true` for validation-only flows. |
| `config[key]`, `key in config`, `config.attr` | Access final merged config. | Use dictionary-style access when keys may be absent. |

## `flashrag.dataset.Item`

| Attribute or method | Behavior |
| --- | --- |
| `Item(item_dict)` | Stores original row in `data`; copies `id`, `question`, `golden_answers`, `choices`, `metadata`, and `output` with defaults. |
| `update_output(key, value)` | Adds generated or intermediate fields into `output`; rejects core keys such as `id`, `question`, `golden_answers`, `output`, and `choices`. |
| `update_evaluation_score(metric_name, metric_score)` | Stores scores under `output['metric_score'][metric_name]`. |
| `__getattr__` | Reads known fields first, then `output`, then original `data`. |
| `__setattr__` | Assigning a non-core attribute writes into `output`. |
| `to_dict()` | Serializes original data plus cleaned `output` and `metadata`; converts NumPy values and strips images. |

## `flashrag.dataset.Dataset`

| Operation | Behavior | Agent note |
| --- | --- | --- |
| `Dataset(config=None, dataset_path=None, data=None, sample_num=None, random_sample=False)` | Loads data from a path or uses provided `dict`/`Item` list. | If `config` lacks `dataset_name`, FlashRAG uses a default name and warns. |
| `_load_data(dataset_name, dataset_path)` | Requires file existence. Loads `.jsonl` or `.json` line-by-line; loads parquet through Hugging Face datasets with image casting. | Despite `.json` support, the loader expects one JSON object per line, not a single JSON array. |
| `question`, `golden_answers`, `id`, `output` | Properties returning per-item lists. | Missing row fields appear as `None` or default empty lists. |
| `get_batch_data(attr_name, batch_size)` | Yields lists of one attribute by batch. | Attribute lookups follow `Item` fallback behavior. |
| `get_attr_data(attr_name)` | Returns an attribute for all rows. | Useful for generated output fields. |
| `update_output(key, value_list)` | Writes one value per item; lengths must match. | Core fields cannot be overwritten through `Item.update_output`. |
| `save(save_path)` | Writes a JSON array of serialized rows. | Not JSONL; choose the expected format deliberately. |

## Dataset utilities

| Function | Behavior |
| --- | --- |
| `convert_numpy(data)` | Recursively converts NumPy arrays/scalars/strings/bools into JSON-serializable Python values. |
| `filter_dataset(dataset, filter_func=None)` | Returns the original dataset if no filter; otherwise removes items that do not satisfy the function and returns a new `Dataset`. |
| `split_dataset(dataset, split_symbol)` | Splits a dataset into a dict of `Dataset` objects keyed by symbols; `split_symbol` length must equal dataset length. |
| `merge_dataset(dataset_split, split_symbol)` | Reconstructs a dataset from split datasets and original symbol order. |
| `get_batch_dataset(dataset, batch_size=16)` | Yields `Dataset` batches. |
| `merge_batch_dataset(dataset_list)` | Concatenates batches into one dataset using the first config. |
| `remove_images(data)` and `clean_prompt_image(input)` | Remove PIL image objects and image prompt entries before serialization. |

## Runtime dependency expectations

A top-level `flashrag` import can succeed while deeper modules still need runtime packages. Config and dataset work commonly needs PyYAML, NumPy, Torch, Hugging Face datasets for parquet, and PIL for some serialization paths. The bundled validator avoids these imports so agents can check file shape before installing or loading heavy dependencies.
