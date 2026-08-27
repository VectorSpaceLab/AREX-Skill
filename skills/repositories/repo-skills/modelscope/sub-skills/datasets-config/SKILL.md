---
name: datasets-config
description: "Operate ModelScope dataset loading, file IO, and config parsing
  workflows safely, especially local/offline recipes and trust_remote_code
  gates."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# datasets-config

Use this sub-skill when a task needs ModelScope data or configuration setup before modeling work:

- Load small inline lists, local files or directories, Hugging Face packaged/local datasets, Hugging Face Hub datasets, or ModelScope Hub datasets with `MsDataset.load`.
- Choose `namespace`, `subset_name`, `split`, `data_files`, `data_dir`, `target`, `download_mode`, `cache_dir`, `token`, `dataset_info_only`, `use_streaming`, and `trust_remote_code` deliberately.
- Read or write JSON/YAML/YML recipe files with `modelscope.fileio.load`, `dump`, and `dumps`.
- Parse, inspect, and override ModelScope `Config` objects with `Config.from_file`, `from_string`, `safe_get`, and `merge_from_dict`.
- Validate a local/offline dataset recipe before running a load command.

Route downstream training, evaluation loops, metrics, Trainer setup, or torch/tensor conversion after a dataset is loaded to `../training-and-evaluation/SKILL.md`. Route Hub snapshot download command mechanics, CLI login, repository clone/push workflows, or broad Hub command usage to `../hub-and-cli/SKILL.md`.

## Read first

1. `references/api-reference.md` for `MsDataset.load`, file IO, upload/delete deprecation, and source-mode routing.
2. `references/data-formats.md` for local/offline examples, `data_files` shapes, column mapping, and recipe schema.
3. `references/configuration.md` for JSON/YAML/Python config behavior and remote-code trust gates.
4. `references/troubleshooting.md` when errors mention unsupported formats, missing paths, streaming, split/config discovery, or remote-code refusal.

## Safe local recipe check

Before running a local recipe supplied by a user or produced by another agent:

```bash
python scripts/validate_dataset_recipe.py path/to/dataset_recipe.yaml
```

The script performs static validation only: it does not import ModelScope, does not contact remote Hubs, does not download data, does not train, and does not write outside its process. Use it to catch missing local files, unsupported `fileio` formats, unsafe `.py` config loads, accidental `streaming=` kwargs, unknown remote URIs in local recipes, and mismatched `target` or `column_mapping` columns when headers can be inferred.

## Operating rules

- Prefer local/offline examples for drafting code. Mark Hugging Face Hub and ModelScope Hub examples as requiring network and credentials when applicable.
- Use `use_streaming=True` with `MsDataset.load`; do not pass a separate `streaming=` keyword to `MsDataset.load` because it can collide with ModelScope's own forwarding.
- Treat `.py` dataset scripts and `.py` config files as executable code. Require explicit `trust_remote_code=True` only when the source is known and trusted. JSON/YAML configs are passive data.
- Use `target` only when iteration should yield a single column value instead of full examples. For renaming columns, load first, then use the underlying Hugging Face-style dataset operations described in `references/data-formats.md`.
- Treat deprecated dataset upload/delete helpers as legacy. Prefer Hub API methods or the ModelScope CLI; use the Hub/CLI sub-skill for command mechanics.
