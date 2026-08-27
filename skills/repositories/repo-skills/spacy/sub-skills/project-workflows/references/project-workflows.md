# Project workflows

This reference covers spaCy project operations backed by `project.yml`: cloning a template, downloading assets, running commands and workflows, generating docs, generating DVC config, and syncing outputs to remotes.

## Safe default flow
1. Validate the local `project.yml`.
2. Review the project docs with `project document`.
3. Dry-run the command or workflow with `project run --dry`.
4. Fetch assets, using `--extra` only for opt-in assets.
5. Run the smallest command that covers the change.
6. Push or pull outputs only after the remote is confirmed.
7. Generate DVC config only when DVC is installed and initialized.

## Command map

| Command | Preview-safe? | Side effects | Use when |
| --- | --- | --- | --- |
| `project clone` | No | Git clone / sparse checkout | Starting from a template or a custom repo. |
| `project assets` | Partly | Downloads or copies assets | Fetching datasets, weights, or other project files. |
| `project run --dry` | Yes | None | Checking command order, skip logic, and path wiring. |
| `project run` | No | Executes scripts and updates outputs | Running one command or a workflow for real. |
| `project document` | Yes | Writes or updates `README.md` | Generating project documentation from `project.yml`. |
| `project dvc` | Yes after DVC init | Writes `dvc.yaml` | Generating a DVC pipeline from one workflow. |
| `project push` | No | Uploads outputs to remote storage | Saving outputs for reuse or sharing. |
| `project pull` | No | Downloads matching outputs from remote storage | Restoring outputs that are missing locally. |

## When to use `--dry`, `--force`, and `--extra`

| Flag | Meaning | Typical use |
| --- | --- | --- |
| `--dry` | Parse the project plan without executing scripts | Inspecting a workflow before the first real run, or checking a project after edits. |
| `--force` | Re-run even if deps and outputs look unchanged | Recomputing outputs after a manual change or when you want a fresh run. |
| `--extra` | Fetch only opt-in assets | Large assets that should not download during the default asset pass. |

## Project lifecycle notes

### `project clone`
- Clones from the default projects repo unless `--repo` is set.
- Use `--branch` when the template lives on a non-default branch.
- Can target a template path inside the repo.
- `--sparse` reduces checkout size when Git supports sparse checkout.
- Treat clone as networked setup, not as a validation step.

### `project assets`
- Fetches assets listed in `project.yml`.
- URL-based assets may use remote storage or Git sparse checkout.
- Use `--sparse` for Git-backed assets when the repository is large and your Git version supports sparse checkout.
- Local-path assets are copied into the project.
- Assets marked `extra: true` are skipped unless `--extra` is set.
- Private assets without a URL or Git block are placeholders that must be provided locally.

### `project run`
- Runs a named command or workflow.
- Uses `deps` and `outputs` to decide whether a command can be skipped.
- Writes and updates `project.lock` with command and file hashes.
- Does not automatically run upstream commands if a dependency is missing.
- Commands without outputs always run; commands with `no_skip: true` also always run.
- `project run --dry` is the safest way to inspect a new workflow.

### `project document`
- Generates a Markdown README from the project file.
- Only the auto-generated section is replaced when markers already exist.
- If no auto-generated block exists, the output file can be replaced.
- Use `--output` to choose the target file and `--no-emoji` for plain titles.

### `project dvc`
- Generates a `dvc.yaml` file for one workflow.
- Requires DVC to be installed and initialized in the project.
- DVC tracks a single pipeline per generated config, so choose the workflow carefully.
- Re-run `project dvc` when the project file changes.
- Use `--force` when you need to regenerate the DVC file from scratch.

### `project push`
- Uploads outputs to a configured remote.
- Uses the command string, dependency hashes, and output content to avoid overwriting old versions.
- Creates new versions instead of mutating existing remote state.
- Keep remote cleanup separate from the push step.

### `project pull`
- Downloads outputs that are missing locally and match the stored command/dependency hashes.
- Avoids stale results when the command or inputs have changed.
- Restores historical outputs without overwriting remote versions.

## Dependency and output tracking
- Declare `deps` for every file a command needs.
- Declare `outputs` for every file or directory a command produces.
- Use relative paths for project-local files.
- Commands with changed deps or outputs rerun; unchanged commands can be skipped.
- `project run` does not infer a full dependency graph, so it will not auto-run earlier steps.
- If a command must always run, use `no_skip: true` instead of relying on missing outputs.
- `outputs_no_cache` is the DVC-friendly alternative when you do not want cached outputs tracked as normal artifacts.

## Remote storage and network boundaries
- Asset URLs, Git-backed assets, `project push`, and `project pull` can all require network access.
- Remote storage may also need provider-specific credentials or extra protocol dependencies.
- A local file remote is the safest remote to use for dry validation.
- `project run --dry` does not fetch assets or authenticate to a remote.

## Minimal local recipe

```bash
python scripts/validate_project_yml.py project.yml
python -m spacy project document --output README.md
python -m spacy project run all --dry
python -m spacy project assets --extra
python -m spacy project run all
python -m spacy project push default
python -m spacy project pull default
python -m spacy project dvc all
```

## When this should hand off to another sub-skill
- If a workflow command calls `spacy train`, `spacy convert`, `spacy evaluate`, or `spacy package`, read `training-and-cli` for those command details.
- If a workflow script defines custom pipeline factories or component registration, read `pipeline-components` for those APIs.
- If asset, clone, push, or pull behavior fails before the project plan runs, use the troubleshooting reference first.
