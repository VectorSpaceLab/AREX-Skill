# Sharing and Hub Reference

This reference covers operational Hub publishing with `datasets`, not general dataset loading, schemas, or processing. Use sibling sub-skills for those topics.

## Choose the Publishing Path

- Use `Dataset.push_to_hub(...)` or `DatasetDict.push_to_hub(...)` when the dataset already exists as an in-memory `Dataset`/`DatasetDict` and should be serialized, sharded, committed, and optionally documented through Datasets APIs.
- Use `huggingface-cli upload ... --repo-type dataset` when syncing a folder or individual files directly to a dataset repository.
- Use the Hub web UI for small manual uploads or dataset card edits.
- Use `datasets-cli delete_from_hub` only to remove a supported data-only dataset configuration; it is not a generic repository deletion command.

## `push_to_hub` Planning Checklist

Plan these before running network-mutating upload code:

- `repo_id`: Use `user_or_org/dataset_name` for organization uploads; avoid ambiguous bare names in automation.
- `private`: Set only when creating a repository or when privacy is explicitly required.
- `token`: Prefer `token=True` or a configured login token with write permission; do not embed token strings in examples, logs, notebooks, or skill artifacts.
- `config_name`: Use for subsets/configurations. Use a stable value such as `default`, `en`, `full`, or `sampled`.
- `set_default`: Use when a multi-config repo needs one config loadable without a config argument.
- `split`: Use when pushing a single `Dataset` as a named split. For `DatasetDict`, splits come from dictionary keys.
- `data_dir`: Use to isolate files within a repository when maintaining multiple layouts or staged uploads.
- `revision`: Target a branch, tag, or PR ref when needed; use with care because it determines where commits land.
- `create_pr`: Prefer `True` for high-risk updates, third-party repositories, or review workflows.
- `commit_message` / `commit_description`: Include dataset version, source snapshot, schema changes, and validation notes.
- `max_shard_size` / `num_shards`: Control upload shard sizes for large datasets; avoid excessive shard counts that can create too many commits or slow Hub operations.
- `embed_external_files`: Keep `True` when examples reference external media/files that must be embedded for portability; consider `False` only when external paths are intentionally stable and accessible.
- `num_proc`: Use for parallel serialization/uploads after verifying the environment and storage can tolerate the concurrency.

The verified public API shape includes:

```python
Dataset.push_to_hub(
    repo_id,
    config_name="default",
    set_default=None,
    split=None,
    data_dir=None,
    commit_message=None,
    commit_description=None,
    private=None,
    token=None,
    revision=None,
    create_pr=False,
    max_shard_size=None,
    num_shards=None,
    embed_external_files=True,
    num_proc=None,
)
```

`DatasetDict.push_to_hub` exposes the same repository, config/data_dir, auth, revision/PR, sharding, embedding, and parallelism concepts across all splits.

## Safe Multi-config Private Upload Pattern

Use this pattern as a plan, not as a token-bearing copy/paste block:

```python
from datasets import DatasetDict

repo_id = "my-org/my-private-dataset"
common = {
    "repo_id": repo_id,
    "private": True,
    "token": True,
    "create_pr": True,
    "commit_message": "Add curated dataset configs",
    "max_shard_size": "500MB",
}

DatasetDict({"train": train_ds, "validation": valid_ds}).push_to_hub(
    config_name="default",
    set_default=True,
    data_dir="default",
    **common,
)
DatasetDict({"train": train_small, "test": test_small}).push_to_hub(
    config_name="sampled",
    data_dir="sampled",
    **common,
)
```

Safety notes:

- Keep `token=True`; do not materialize the token in code.
- Use `create_pr=True` until repository owners review the layout and card metadata.
- Use distinct `config_name` and `data_dir` values so generated files do not collide.
- Validate loadability from the PR or branch before merging when practical.

## Dataset Repository Structure

A data-only dataset repository normally contains data files and a `README.md` dataset card.

Simple split inference works for files such as:

```text
README.md
train.csv
test.csv
```

For non-trivial layouts, put a YAML frontmatter block in `README.md` with `configs`. Always include `config_name`, even for a single explicit config:

```yaml
---
configs:
- config_name: default
  data_files:
  - split: train
    path: "data/train/*.parquet"
  - split: validation
    path: "data/validation/*.parquet"
  default: true
---
```

Use multiple configs for subsets:

```yaml
---
configs:
- config_name: main
  data_files: "main_data.csv"
  default: true
- config_name: supplemental
  data_files: "additional_data.csv"
---
```

Route schema details to `../../features-formats/SKILL.md`; this sub-skill only owns Hub repository/card structure.

## Dataset Card Essentials

A good `README.md` card should contain:

- YAML metadata for discoverability: license, language, task categories, pretty name, size category, and `configs` when needed.
- Dataset summary, intended uses, limitations, biases, licensing, citation, and point of contact.
- Clear structure notes: configs, splits, file formats, and any known missing or filtered data.
- Responsible-use notes for privacy, PII, consent, or sensitive content.

Use `../scripts/dataset_card_minimal.md` as a compact self-contained starting point. Do not leave placeholder metadata in a published card when reliable values are known.

## Hub CLI Upload Notes

`huggingface-cli upload` is provided by `huggingface_hub`, not `datasets-cli`, but it is often the safest way to upload prepared folders:

```bash
huggingface-cli upload user_or_org/dataset_name ./local_dataset . --repo-type dataset --create-pr --commit-message "Upload curated data"
```

Useful options include `--include`, `--exclude`, `--delete`, `--revision`, `--create-pr`, `--commit-message`, `--commit-description`, `--token`, `--quiet`, and `--every`. Treat `--delete` as destructive and require explicit confirmation of the patterns.

## Revisions and Pull Requests

- Use `revision="branch-name"` or a PR ref when writing to a non-main branch.
- Use `create_pr=True` in `push_to_hub` when changes should be proposed rather than pushed directly.
- For `huggingface-cli upload`, use `--create-pr` for review workflows.
- If a branch or revision does not exist, some Hub upload flows may create it from `main`; make that explicit in automation.

## Boundary Reminders

- Loading the published dataset is owned by `../../loading-local-hub/SKILL.md`.
- Feature schemas and format-specific details are owned by `../../features-formats/SKILL.md`.
- Transforming, streaming, and preparing the in-memory dataset before upload is owned by `../../processing-streaming/SKILL.md`.
