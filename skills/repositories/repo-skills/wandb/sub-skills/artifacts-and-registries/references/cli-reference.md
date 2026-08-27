# Artifact CLI Reference

The `wandb artifact` group uploads, downloads, lists, and manages the local artifact cache. Commands require the `wandb` console script and generally require W&B credentials for server operations.

## Command overview

```bash
wandb artifact --help
wandb artifact put --help
wandb artifact get --help
wandb artifact ls --help
wandb artifact cache cleanup --help
```

`wandb artifact` subcommands:

- `put`: Upload a local file, local directory, or URL reference as a versioned artifact.
- `get`: Download an artifact by path.
- `ls`: List the latest artifact collections in a project, optionally filtered by type.
- `cache cleanup`: Reclaim local artifact cache space.

## Upload with `put`

Syntax:

```bash
wandb artifact put [OPTIONS] PATH
```

Important options:

- `--name`, `-n`: Artifact name in `project/artifact_name` format. Defaults to the basename of `PATH`; if no project is parsed, the CLI prompts for one.
- `--description`, `-d`: Artifact description.
- `--type`, `-t`: Artifact type. Defaults to `dataset`.
- `--alias`, `-a`: Alias to apply. Can be repeated; defaults to `latest`.
- `--id`: Upload to an existing run ID.
- `--resume`: Resume the last run from the current directory.
- `--skip_cache`: Skip caching while uploading artifact files.
- `--policy`: `mutable` or `immutable`; defaults to `mutable`.

Examples:

```bash
wandb artifact put --type dataset ./data/training
wandb artifact put --name foobar/trained-model --type model ./model.pt
wandb artifact put --alias latest --alias v2.0 --type model ./model.pt
wandb artifact put --type dataset s3://example-bucket/datasets/training
wandb artifact put --type dataset --description "Training data" ./data/training
```

Path behavior:

- Local directories call the same underlying `Artifact.add_dir()` flow.
- Local files call `Artifact.add_file()`.
- Any `PATH` containing `://` is logged as a reference with `Artifact.add_reference()` and is not uploaded as bytes.
- A missing non-URI path fails with `Path argument must be a file or directory`.

## Download with `get`

Syntax:

```bash
wandb artifact get [OPTIONS] PATH
```

Options:

- `--root`: Directory to download the artifact to. Uses the default artifact directory/cache behavior if omitted.
- `--type`: Expected artifact type; fails when the fetched artifact has a different type.

Path format:

- `entity/project/artifact_name:version`
- `entity/project/artifact_name:alias`
- If the version/alias is omitted, the CLI uses `latest`.

Examples:

```bash
wandb artifact get team-awesome/foobar/processed-training-set:latest
wandb artifact get --root ./data team-awesome/foobar/processed-training-set:v2
wandb artifact get --type model team-awesome/models/classifier:prod
```

For registry artifacts, the CLI handles registry-project paths and organization/entity resolution internally. Use explicit full paths when debugging ambiguous defaults.

## List with `ls`

Syntax:

```bash
wandb artifact ls [OPTIONS] PATH
```

Options:

- `--type`, `-t`: Filter artifact collections by type.

`PATH` is an `entity/project` pair. The command displays each latest collection version with type, updated time, size, and collection name.

Examples:

```bash
wandb artifact ls team-awesome/foobar
wandb artifact ls --type model team-awesome/foobar
```

If a collection exists but has no versions, the CLI displays `N/A`, `0 B`, and `(no versions)` for that collection.

## Cache cleanup

Syntax:

```bash
wandb artifact cache cleanup [OPTIONS] TARGET_SIZE
```

Options:

- `TARGET_SIZE`: Desired cache size such as `10GB` or `500MB`.
- `--remove-temp/--no-remove-temp`: Also remove temporary files from the cache; defaults to `--no-remove-temp`.

Examples:

```bash
wandb artifact cache cleanup 10GB
wandb artifact cache cleanup --remove-temp 5GB
```

## Credential and mode checks

- Run `wandb login` or set `WANDB_API_KEY` before commands that contact W&B.
- Use `wandb status` to confirm the active entity/project/mode when CLI path resolution is surprising.
- `wandb offline` affects run syncing behavior, but artifact downloads and registry operations still need server access when fetching remote content.
- For self-hosted W&B, configure the host with `wandb login --host ...` or `WANDB_BASE_URL` before artifact operations.

## CLI path debugging checklist

1. Expand shorthand paths to `entity/project/artifact:alias` or `entity/project/artifact:vN`.
2. Confirm whether `project` is a normal project or a registry project such as `wandb-registry-model`.
3. Check `--type` only after the path resolves; a type mismatch can mask an otherwise valid artifact path.
4. Confirm credentials before assuming the artifact is missing.
5. Use version pins for reproducibility; use aliases for moving channels.
