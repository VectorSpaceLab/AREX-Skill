# `clearml-data` CLI Reference

`clearml-data` is the Dataset Management & Versioning CLI. It creates, mutates, uploads, finalizes, retrieves, verifies, compares, and lists ClearML datasets.

The CLI restores and writes session state in `~/.clearml_data.json`. After `create`, it stores the new dataset ID. Later commands without `--id` may use that stored ID. For reproducible instructions, include `--id DATASET_ID` on all mutating commands after creation.

Use `../scripts/dataset_cli_plan.py` to build command sequences without running them.

## Global Shape

```bash
clearml-data {create,add,set-description,sync,remove,upload,close,publish,delete,rename,move,compare,squash,search,verify,list,get} ...
```

Common safe lifecycle:

```bash
clearml-data create --project PROJECT --name NAME --version VERSION --storage STORAGE_URI
clearml-data add --id DATASET_ID --dataset-folder DATASET_FOLDER --files LOCAL_PATH [LOCAL_PATH ...]
clearml-data upload --id DATASET_ID --storage STORAGE_URI --verbose
clearml-data close --id DATASET_ID --verbose
```

## Create

```bash
clearml-data create \
  --project PROJECT \
  --name NAME \
  --version VERSION \
  --parents PARENT_ID [PARENT_ID ...] \
  --storage STORAGE_URI \
  --tags TAG [TAG ...]
```

Required: `--name`.

Optional:

- `--project PROJECT`: dataset project name.
- `--version VERSION`: dataset semantic or user version.
- `--parents ...`: parent dataset IDs to merge/inherit from.
- `--storage STORAGE_URI`: remote storage for dataset files; supports `s3://`, `gs://`, `azure://`, and shared paths.
- `--output-uri OUTPUT_URI`: deprecated alias for storage; prefer `--storage`.
- `--tags ...`: dataset user tags.

State behavior: writes the created ID into `~/.clearml_data.json`.

## Add Files or Links

```bash
clearml-data add --id DATASET_ID --files PATH [PATH ...]
clearml-data add --id DATASET_ID --dataset-folder train --files data/train --wildcard "*.jpg"
clearml-data add --id DATASET_ID --dataset-folder raw --links s3://bucket/raw gs://bucket/raw
```

Options:

- `--id DATASET_ID`: dataset to mutate; if omitted, the CLI falls back to state.
- `--dataset-folder PATH`: logical path inside the dataset root.
- `--files PATH [PATH ...]`: local files or folders to add.
- `--links URI [URI ...]`: external links to add without copying local files.
- `--wildcard PATTERN [PATTERN ...]`: include only matching files.
- `--non-recursive`: disable recursive file scans.
- `--max-workers N`: thread count for file scanning.
- `--verbose`: print parsed arguments and progress.

Use `--links` for existing remote objects that should be referenced rather than uploaded as ClearML-managed copies.

## Sync

```bash
clearml-data sync --id DATASET_ID --folder LOCAL_FOLDER --dataset-folder DATASET_FOLDER --skip-close
clearml-data sync --folder data/train --project PROJECT --name NAME --version VERSION --storage STORAGE_URI
```

Required: `--folder`.

Behavior:

- If `--parents` or both `--project` and `--name` are provided, `sync` first creates a dataset and then syncs into it.
- It calls `Dataset.sync_folder()` and prints removed/added/modified counts.
- Unless `--skip-close` is set, it uploads pending changes and finalizes the dataset.
- If it created a dataset and found zero modifications, it deletes the empty created dataset.

Options include `--id`, `--dataset-folder`, `--folder`, `--parents`, `--project`, `--name`, `--version`, `--storage`, `--tags`, `--skip-close`, `--chunk-size`, and `--verbose`.

Use `sync` for one-command folder mirroring. Use separate `create` + `add` + `upload` + `close` when the user needs an auditable plan or wants to avoid accidental upload/finalization.

## Upload and Close

Upload pending files without finalizing:

```bash
clearml-data upload --id DATASET_ID --storage STORAGE_URI --chunk-size 512 --max-workers 4 --verbose
```

Finalize, auto-uploading pending files by default:

```bash
clearml-data close --id DATASET_ID --storage STORAGE_URI --chunk-size 512 --max-workers 4 --verbose
```

Finalize only if everything is already uploaded:

```bash
clearml-data close --id DATASET_ID --disable-upload
```

Important state behavior:

- `upload` does not clear CLI state.
- `close` clears CLI state after successful finalization.
- `close --disable-upload` raises an error when the dataset has pending uploads.
- `close` without `--disable-upload` calls upload automatically when `Dataset.is_dirty()` is true.

## Get, List, Verify, Compare

Read-only cached copy:

```bash
clearml-data get --id DATASET_ID
```

Writable copy:

```bash
clearml-data get --id DATASET_ID --copy output_folder --overwrite
```

Soft link to read-only cached copy:

```bash
clearml-data get --id DATASET_ID --link linked_folder --overwrite
```

Partial copy:

```bash
clearml-data get --id DATASET_ID --part 0 --num-parts 4
```

List content:

```bash
clearml-data list --id DATASET_ID --filter "train/*.jpg"
clearml-data list --project PROJECT --name NAME --version VERSION --modified
```

Verify local content:

```bash
clearml-data verify --id DATASET_ID --folder LOCAL_COPY --verbose
clearml-data verify --id DATASET_ID --folder LOCAL_COPY --filesize
```

Compare versions:

```bash
clearml-data compare --source BASE_DATASET_ID --target CHILD_DATASET_ID --verbose
```

## Search and Management

Search:

```bash
clearml-data search --project PROJECT --name PARTIAL_NAME --tags TAG_A TAG_B
clearml-data search --ids ID_A ID_B --not-only-completed
```

Squash versions:

```bash
clearml-data squash --name NEW_NAME --ids ID_A ID_B ID_C --storage STORAGE_URI
```

Administrative operations:

```bash
clearml-data publish --id DATASET_ID
clearml-data delete --id DATASET_ID --force
clearml-data rename --project PROJECT --name OLD_NAME --new-name NEW_NAME
clearml-data move --project PROJECT --name NAME --new-project NEW_PROJECT
```

Treat `delete`, `rename`, `move`, `publish`, and `squash` as state-changing operations. Do not suggest them unless the user explicitly asks or confirms intent.

## Safe Command Construction

- Quote every shell argument with `shlex.quote()` or equivalent when generating commands.
- Include `--id` after creation whenever commands may run in separate shells.
- Prefer `--storage` over deprecated `--output-uri`.
- Avoid embedding credentials in `--storage`; use configured cloud credentials.
- Use `--skip-close` on `sync` when the user wants to inspect before upload/finalize.
- Use `--disable-upload` on `close` only when you know `upload` already succeeded.
- Use `--dataset-folder` to prevent local directory names from becoming surprising dataset paths.
- Use `--non-recursive` only for single-level adds/removes; recursive is the default.

## Parent/Child Command Skeleton

For a child version that references two finalized parents and does not upload immediately:

```bash
clearml-data create --project PROJECT --name CHILD_NAME --version CHILD_VERSION --parents PARENT_A_ID PARENT_B_ID --storage s3://bucket/path
clearml-data add --id CHILD_DATASET_ID --dataset-folder train --files local/train
clearml-data add --id CHILD_DATASET_ID --dataset-folder test --files local/test
clearml-data upload --id CHILD_DATASET_ID --storage s3://bucket/path --verbose
clearml-data close --id CHILD_DATASET_ID --disable-upload --verbose
```

If the user explicitly says not to run uploads, stop after planning the commands or mark `upload`/`close` as optional manual steps.
