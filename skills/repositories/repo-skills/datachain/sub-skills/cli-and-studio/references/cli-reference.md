# DataChain CLI Reference

## Purpose

Read this reference to choose the correct `datachain` command family, understand
key flags, and avoid mixing storage paths with saved dataset names. Commands are
shown as reusable patterns with placeholders; replace placeholders with the
user's real non-secret values.

## Global Parser Behavior

```bash
datachain --help
datachain -V
# Command-scoped verbosity flags appear after the command/subcommand:
datachain ls -v s3://bucket/path/
datachain job run -q query.py
```

- `-V` / `--version` prints the installed DataChain package version.
- `-v` / `--verbose` increments verbosity; any positive value maps logging to
  debug level.
- `-q` / `--quiet` suppresses ordinary logging by using a critical-only level.
- `datachain` with no command prints top-level help to stderr and exits nonzero.
- Most command families support `datachain <command> --help`; nested families
  support `datachain <command> <subcommand> --help`.
- Hidden developer switches such as SQL-debugging or post-mortem debugging exist
  in the parser but should not be part of normal user workflows.

## Storage vs Dataset vs Display

| User intent | Use this | Subject shape | Notes |
| --- | --- | --- | --- |
| List, size, search, copy, clone, or index object storage | `ls`, `du`, `find`, `cp`, `clone`, `index`, `bucket status` | URI/path such as `s3://bucket/prefix`, `gs://...`, `az://...`, `hf://...`, or a local path | These operate on storage entries and local catalog/cache state. |
| List, remove, edit, or pull saved DataChain datasets | `dataset` or `ds` | Dataset name, optionally `namespace.project.name` or `name@version` | Dataset commands operate on registered DataChain datasets, not raw object paths. |
| Inspect rows, schema, or source script for a saved dataset | `show` | Dataset name plus optional version | `show` is for saved datasets; use storage `ls` for files. |
| Authenticate and manage Studio remote execution | `auth`, `job`, `pipeline` | Studio token/team, job IDs, pipeline names, dataset names | Requires Studio configuration or environment variables. |
| Install DataChain bundled coding-agent skills | `skill` | Skill names `core`, `knowledge`, `jobs`; target names | Layout details are owned by sibling `agent-harness`; use the bundled layout helper for dry runs. |

## Local vs Studio Flavor Flags

`ls` and `dataset ls` can read local state, Studio state, or both:

- No `--studio`, `--local`, or `--all` flag defaults to **local only**, even if a
  Studio token is configured.
- `--studio` selects Studio and requires a token. Without auth the CLI raises a
  not-logged-in error.
- `-L` / `--local` selects local state explicitly.
- `-a` / `--all` selects both local and Studio when a token is available; without
  a token it falls back to local.
- Passing both `--local` and `--studio` is allowed and displays both sources.
- `--team` applies to Studio reads and mutations; omit it only when the configured
  or environment-provided default team is correct.

## Storage Commands

### `bucket status` — read-only bucket existence/access probe

```bash
datachain bucket status s3://bucket-name/
datachain bucket status gs://bucket-name/
datachain bucket status --account-name STORAGE_ACCOUNT az://container-name/
```

Purpose: checks whether a bucket/container exists and what access level is
visible without listing objects. It returns success when the bucket exists and
nonzero when it is not found; network or credential errors may still raise.
`--account-name` is for Azure anonymous-access detection.

### `ls` — storage listing

```bash
datachain ls [--anon] [-u] [-l] [--studio | --local | --all] [--team TEAM] [SOURCE ...]
```

- With sources, lists files/directories for each storage path.
- Without sources in local mode, lists known local storage listings from the
  DataChain catalog.
- `-l` / `--long` adds timestamp-like long-format details when available.
- `-u` / `--update` refreshes cached listing information and can mutate local
  cache/catalog state.
- `--anon` requests anonymous storage access for public buckets only.
- `--studio` sends listing requests to Studio for the selected team.

### `du` — storage usage summary

```bash
datachain du [--anon] [-u] [-b] [-d N] [--si] SOURCE [SOURCE ...]
```

- `-b` / `--bytes` prints raw bytes.
- `-d N` / `--depth N` / `--max-depth N` controls directory depth; default `0`
  summarizes each provided directory only.
- `--si` prints powers of 1000 instead of powers of 1024.
- `-u` may refresh cached listing metadata.

### `find` — storage search

```bash
datachain find [--anon] [-u] [--name PAT] [--iname PAT] [--path PAT] [--ipath PAT] \
  [--size SPEC] [--type f|d] [-c path,name,size,type,du] SOURCE [SOURCE ...]
```

- `--name` and `--iname` match filenames; `--path` and `--ipath` match paths.
- `--iname` and `--ipath` are case-insensitive.
- `--size` accepts byte counts or suffixed values such as `+10M` or `-100K`.
- `--type f` selects files; `--type d` selects directories.
- `-c` / `--columns` is comma-separated. Valid columns are `path`, `name`,
  `size`, `type`, and `du`; default is `path`. Invalid column names are parser
  errors.

### `index` — register/index storage in local catalog

```bash
datachain index [--anon] [-u] SOURCE [SOURCE ...]
```

Purpose: indexes a storage location in the local DataChain catalog. Treat it as
mutating local DataChain state because it records or refreshes listing metadata.
Use `ls` or `bucket status` first when access is uncertain.

### `cp` — copy storage objects to an output path

```bash
datachain cp [--anon] [-u] [-f] [-r] [--no-glob] SOURCE [SOURCE ...] OUTPUT
```

Purpose: copies data files from storage to a local output directory or file.
Treat it as mutating the filesystem.

- `-r` / `-R` / `--recursive` is required for directory-style copies.
- `-f` / `--force` overwrites or creates outputs even when conflicts exist.
- `--no-glob` disables wildcard expansion for characters such as `*` or `?`.
- `-u` may update local cached listing metadata before copying.

### `clone` — copy storage and create/register a local dataset

```bash
datachain clone [--anon] [-u] [-f] [-r] [--no-glob] [--no-cp] SOURCE [SOURCE ...] OUTPUT
```

Purpose: clones storage data into a local output and registers a dataset in the
local DataChain catalog. Treat it as mutating both filesystem and DataChain
state. `--no-cp` creates the dataset/catalog entry without copying file content.

## Dataset Commands

`dataset` and `ds` are aliases.

### `dataset ls` — list registered datasets

```bash
datachain dataset ls [NAME] [--versions] [--studio | --local | --all] [--team TEAM] [--include-removed]
datachain ds ls [NAME] --versions
```

- Default is local-only unless a flavor flag is provided.
- Without `--versions`, output groups datasets to the latest semantic version.
- Passing `NAME` forces version-aware listing for that dataset.
- `--include-removed` includes removed local/Studio versions where supported.
- Combined local+Studio output shows separate Studio and Local columns.

### `dataset pull` — pull a Studio dataset into local state

```bash
datachain dataset pull DATASET [-o OUTPUT] [-f] [-r] [--cp] [--local-name NAME] [--local-version VERSION]
```

Purpose: pulls a specific remote dataset version from Studio into the local
DataChain DB. Add `--cp` only when actual files should also be copied; then
`-o`, `-r`, and `-f` affect the copied outputs. Treat this as mutating local
DataChain state and possibly the filesystem.

### `dataset edit` — edit dataset metadata

```bash
datachain dataset edit NAME [--new-name NAME] [--description TEXT] [--attrs ATTR [ATTR ...]] [--team TEAM]
```

Purpose: updates dataset metadata. Local datasets are edited locally. A
non-local fully qualified dataset routes to Studio and requires Studio auth and
team context. Confirm the target dataset before changing names or attributes.

### `dataset rm` / `dataset remove` — remove a dataset version or dataset

```bash
datachain dataset rm NAME [--version VERSION] [--force | --no-force] [--studio] [--team TEAM]
datachain dataset remove NAME@VERSION --studio --team TEAM
```

Purpose: removes local dataset state by default. With `--studio`, removes the
Studio dataset/version for the selected team. Treat this as destructive. Prefer
specifying a version explicitly unless the user's intent is to affect all
versions; `--force` deletes registered datasets with all versions where the
backend supports it.

## Display Command

### `show` — inspect a saved dataset

```bash
datachain show NAME [--version VERSION] [--limit N] [--offset N] \
  [--columns col1,col2] [--no-collapse] [--hidden] [--schema] [--script]
```

- Shows rows from a saved dataset. It does not list object-storage paths.
- `--columns` is comma-separated and de-duplicates repeated columns.
- `--limit` defaults to `10`; `--offset` defaults to `0`.
- `--schema` appends schema output after row display.
- `--hidden` includes hidden fields.
- `--script` prints the dataset version's query script and returns without row
  display.

## Maintenance Commands

```bash
datachain gc [--checkpoint-ttl SECONDS]
datachain clear-cache
```

- `gc` garbage-collects temporary tables, failed dataset versions, and outdated
  checkpoints. `--checkpoint-ttl` sets the checkpoint age threshold in seconds;
  the default TTL is four hours.
- `clear-cache` clears the local file cache.
- Both commands mutate local DataChain-managed state. Do not run them only to
  inspect status.

## Studio Command Families

Use [Studio and jobs](studio-and-jobs.md) for details.

```bash
datachain auth login|logout|team|token
datachain job run|ls|logs|cancel|clusters
datachain pipeline create|list|status|pause|resume|remove-job
```

Studio commands require a token and default team from configuration or
`DATACHAIN_STUDIO_*` environment variables unless the command itself is creating
or removing those settings.

## Agent Skill Commands

```bash
datachain skill list
datachain skill install [core,knowledge,jobs] --target claude|cursor|codex|pi|copilot [--local]
datachain skill uninstall [core,knowledge,jobs] --target claude|cursor|codex|pi|copilot [--local]
```

- `skill list` prints the bundled skill names (`core`, `knowledge`, `jobs`) and
  supported targets.
- Omitting the skill list installs or uninstalls all bundled skills.
- `install` and `uninstall` mutate target agent directories. Use the bundled
  [skill layout helper](../scripts/skill_layout_check.py) before the first
  mutation.
- Target-specific layout details, placeholder behavior, knowledge-base methods,
  and installed skill contents are owned by sibling
  [`agent-harness`](../../agent-harness/SKILL.md).

## Completion Command

```bash
datachain completion --shell bash
```

`completion` emits shell completion scripts using the selected shell name. It is
read-only but shell-specific; inspect its help before writing the result into a
shell startup file.
