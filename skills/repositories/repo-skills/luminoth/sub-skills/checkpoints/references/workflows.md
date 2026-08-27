# Checkpoint Workflows

## Purpose

Use this reference for local checkpoint inspection, remote index refreshes,
checkpoint download/import/export, and packaging a finished run.

## Local storage layout

Luminoth stores checkpoint state under `LUMI_HOME`, which defaults to
`~/.luminoth`.

Important paths:

- `~/.luminoth/checkpoints/checkpoints.json` — checkpoint index
- `~/.luminoth/checkpoints/<checkpoint-id>/` — checkpoint files and config

The local index stores both local and remote checkpoints, plus aliases and
status fields.

## Common commands

```bash
lumi checkpoint list
lumi checkpoint info accurate
lumi checkpoint refresh
lumi checkpoint download accurate
lumi checkpoint create ./config.yml -e name='My checkpoint' -e alias=my-alias
lumi checkpoint edit my-alias -e description='Updated description.'
lumi checkpoint export my-alias --output ./exports
lumi checkpoint import ./exports/<checkpoint-id>.tar
lumi checkpoint delete <checkpoint-id>
```

## Command roles

### `list`

Shows the current local index.

### `info`

Prints a human-readable summary for one id or alias.

### `refresh`

Fetches the remote checkpoint index and merges it into the local index.
Use this when you need to discover newly published remote checkpoints.

### `download`

Downloads a remote checkpoint tarball into the local checkpoint directory.
The command refuses to download a checkpoint that is already local.

### `create`

Packages the latest TensorFlow checkpoint from a training run into a new local
checkpoint record.
It reads `train.job_dir` and `train.run_name` from the config, then copies the
checkpoint files and `classes.json` if present.

### `edit`

Modifies metadata fields such as `name`, `description`, `alias`, and the dataset
summary fields.

### `delete`

Removes a local checkpoint from the index and deletes its files. For remote
checkpoints it only resets the local download state.

### `export`

Writes a tarball containing the checkpoint files plus a `metadata.json` entry.

### `import`

Reads a tarball previously produced by `export` and adds it to the local index.

## Alias and id rules

- Checkpoints can be addressed by id or alias.
- If an alias collides, the newest local checkpoint wins before remote ones.
- For destructive operations, prefer the exact checkpoint id.

## What prediction does with checkpoints

The prediction sub-skill uses checkpoint lookups to build a model config and
points the dataset/job directory at the checkpoint contents.

## What to read next

- `references/troubleshooting.md` for alias, tar, and path problems.
- `scripts/inspect_checkpoint_index.py` for a safe local inspection helper.
- `../prediction/SKILL.md` if the user wants to use a checkpoint for inference.
