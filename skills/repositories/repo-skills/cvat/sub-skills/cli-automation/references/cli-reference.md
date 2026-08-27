# CVAT CLI reference

This reference summarizes the `cvat-cli` grammar verified from the CVAT CLI package and public CLI documentation. The CLI entry point is `cvat-cli` and Python support starts at 3.10.

## Global command shape

```bash
cvat-cli <global-options> <resource> <action> <action-options>
```

Global options must appear before the resource:

| Option | Meaning | Automation guidance |
|---|---|---|
| `--version` | Print client version and exit. | Use in diagnostics and reproducibility logs. |
| `--insecure` | Disable TLS certificate verification. | Use only for explicitly trusted test/self-hosted servers; document the risk. |
| `--auth USER[:PASS]` | Password authentication. If password is omitted, `PASS` or an interactive prompt is used. | Prefer `--auth USER` plus `PASS` out of band; never write `USER:PASS` into generated scripts. |
| `--server-host URL_OR_HOST` | Server base URL/host. | Include the scheme when possible, e.g. `https://app.cvat.ai`. |
| `--server-port PORT` | Port to append when the selected server URL has no port. | Do not combine with a server URL that already contains a port. |
| `--organization SLUG`, `--org SLUG` | Organization workspace slug. | Required for organization-scoped tasks/projects; an empty string means personal workspace. |
| `--profile NAME` | Saved PAT profile containing both server and credential. | Mutually exclusive with `--server-host`, `--server-port`, and `--auth`. |
| `--debug` | Verbose logging and HTTP debug output. | Use only after redacting logs; debug output can expose request details. |

## Authentication and profile resolution

Supported authentication routes:

1. **Saved profile**: `cvat-cli --profile prod task ls`. A profile stores a server URL and a PAT. This is safest for repeated automation.
2. **Default profile**: if no explicit server/credential is supplied and a default profile exists, the CLI uses it.
3. **Password auth**: `cvat-cli --auth USER task ls`, with `PASS` set out of band or prompt input. `--auth USER:PASS` works but is unsafe for scripts.
4. **PAT environment variable**: `CVAT_ACCESS_TOKEN` supplies a PAT. It is treated as an explicit credential and is prioritized over other authentication environment variables.
5. **Fallback prompt**: without profile, explicit credential, or token, the CLI uses the current OS username and reads `PASS` or prompts for a password.

Server resolution outside profiles:

1. `--server-host`, plus `--server-port` if provided and no port is already embedded.
2. `cvat-cli config default-server` value.
3. Built-in `http://localhost`.

Important profile rule: `--profile` supplies both server and PAT. The CLI rejects mixing it with `--server-host`, `--server-port`, or `--auth`. Supplying an explicit server or credential also prevents borrowing the missing counterpart from the default profile.

### Profile and config commands

```bash
# Create a profile by prompting for the PAT and set it as default.
cvat-cli --server-host https://app.cvat.ai profile create --name prod --set-default

# Create a profile from a plain token file or JSONC token envelope.
cvat-cli --server-host https://app.cvat.ai profile create --name prod --file ~/Downloads/token.txt
cvat-cli profile create --file ~/Downloads/cvat-token-envelope.json

# Override the server embedded in a JSONC envelope.
cvat-cli --server-host https://new.example.com profile create --file ~/Downloads/cvat-token-envelope.json

# Manage profiles.
cvat-cli profile list
cvat-cli profile list --names-only
cvat-cli profile default
cvat-cli profile default prod
cvat-cli profile default --unset
cvat-cli profile delete old-prod

# Manage the fallback server used outside profile mode.
cvat-cli config default-server https://app.cvat.ai
cvat-cli config default-server
cvat-cli config default-server --unset
```

Saved profiles are local PAT profiles only. Deleting a profile does not revoke the token on the CVAT server; revoke leaked or retired tokens through CVAT user settings or the API.

The local profile store is permission-sensitive: on POSIX systems the directory must be `0700` and the JSON store must be `0600`. If the CLI refuses to read it, fix permissions before retrying.

## Resource/action map

| Resource | Actions | Notes |
|---|---|---|
| `task` | `ls`, `create`, `delete`, `frames`, `export-dataset`, `import-dataset`, `backup`, `create-from-backup`, `auto-annotate` | Main automation surface for annotation tasks. |
| `project` | `ls`, `create`, `delete`, `backup`, `create-from-backup`, `export-dataset`, `import-dataset` | Project-level dataset import creates project tasks; labels must be compatible. |
| `function` | `create-native`, `delete`, `run-agent` | Native functions are CVAT Enterprise/Cloud functionality. |
| `profile` | `list`, `default`, `delete`, `create` | Local profile store; normally no server request except optional token-name lookup when no name is supplied. |
| `config` | `default-server` | Local fallback server configuration. |

Deprecated aliases map to task actions only. Avoid them in new scripts:

| Deprecated alias | Replacement |
|---|---|
| `create` | `task create` |
| `ls` | `task ls` |
| `delete` | `task delete` |
| `frames` | `task frames` |
| `dump` | `task export-dataset` |
| `upload` | `task import-dataset` |
| `export` | `task backup` |
| `import` | `task create-from-backup` |
| `auto-annotate` | `task auto-annotate` |

## Task commands

### `task ls`

```bash
cvat-cli --profile prod task ls
cvat-cli --profile prod --org team task ls --json > tasks.json
```

`--json` prints a JSON response suitable for `jq`, Python, or shell validation. Without `--json`, the command prints task IDs.

### `task create`

Exact grammar:

```bash
cvat-cli <global-options> task create NAME [task-options] {local|share|remote} RESOURCE [RESOURCE ...]
```

Key options:

| Option | Meaning |
|---|---|
| `--labels LABELS` | JSON string or path to a JSON labels file. Required unless `--project_id` supplies labels from an existing project. |
| `--project_id ID` | Attach the task to an existing project and use project labels. |
| `--annotation_path PATH` + `--annotation_format FORMAT` | Upload initial annotations while creating the task. Default format is `CVAT 1.1`. |
| `--bug_tracker URL`, `--bug URL` | Link a bug tracker. |
| `--image_quality INT` | Image quality, default `70`. |
| `--chunk_size INT`, `--frame_step INT`, `--overlap INT`, `--segment_size INT`, `--start_frame INT`, `--stop_frame INT` | Advanced data segmentation/frame controls. |
| `--sorting-method lexicographical|natural|predefined|random` | Data sorting method; default `lexicographical`. |
| `--copy_data` | Copy shared data to server storage; only for `share`. |
| `--use_cache`, `--use_zip_chunks` | Enable CVAT data cache or zip chunks. |
| `--cloud_storage_id ID` + `--filename_pattern PATTERN` | Use data from cloud storage with manifest-style filtering. Pattern supports shell wildcards (`*`, `?`, `[seq]`, `[!seq]`). |
| `--completion_verification_period SEC` | Poll interval while waiting for data compression; default `2`. |

Resource types:

- `local`: local files/directories uploaded by the CLI.
- `remote`: URLs fetched by CVAT.
- `share`: paths in the server's shared storage or manifest paths for configured cloud storage.

Examples:

```bash
cvat-cli --profile prod task create "vehicle task" --labels labels.json local img1.jpg img2.jpg

cvat-cli --profile prod --org team task create "project task" --project_id 7 \
  remote https://example.org/videos/sample.mp4

cvat-cli --profile prod task create "shared filtered cloud data" \
  --labels '[{"name":"car"}]' --use_cache --cloud_storage_id 3 --filename_pattern "images/*.jpg" \
  share manifest.jsonl
```

The command prints the new task ID on success.

### `task frames`

```bash
cvat-cli --profile prod task frames --outdir frames --quality compressed 42 0 10 20
cvat-cli --profile prod task frames --quality original 42 100
```

Outputs are named `task_<ID>_frame_<FRAME>.jpg` by default. Use `compressed` for smaller scripting artifacts and `original` when exact source pixels are required.

### `task export-dataset`

```bash
cvat-cli --profile prod task export-dataset --format "CVAT for images 1.1" 42 task-42.zip
cvat-cli --profile prod task export-dataset --format "COCO 1.0" --with-images yes 42 task-42-coco.zip
cvat-cli --profile prod task export-dataset --format "YOLO 1.1" --completion_verification_period 5 42 exports/
```

If `filename` is omitted, the CLI writes into the current directory using the server-generated name. If `filename` ends with a directory separator, the directory is created if needed. `--with-images` uses boolean parsing such as `yes/no`, `true/false`, or `1/0`.

### `task import-dataset`

```bash
cvat-cli --profile prod task import-dataset --format "CVAT 1.1" 42 annotations.xml
cvat-cli --profile prod task import-dataset --format "YOLO 1.1" 42 yolo.zip
```

This imports annotations into an existing task. The task labels must be compatible with the dataset labels. For detailed format selection, route to `../../dataset-ops/SKILL.md`.

### `task backup` and `task create-from-backup`

```bash
cvat-cli --profile prod task backup --completion_verification_period 5 42 task-42-backup.zip
cvat-cli --profile prod task create-from-backup task-42-backup.zip
```

Backups preserve more CVAT-specific state than format exports and are preferred before destructive changes or migrations.

### `task delete`

```bash
cvat-cli --profile prod task ls --json | jq '.results[] | {id, name}'
cvat-cli --profile prod task delete 42 43
```

Deletion ignores IDs that do not exist. Validate the ID list before running.

### `task auto-annotate`

Exact grammar:

```bash
cvat-cli <global-options> task auto-annotate TASK_ID \
  (--function-module MODULE | --function-file PATH) \
  [-p NAME=TYPE:VALUE ...] [--clear-existing] [--allow-unmatched-labels] \
  [--conf-threshold FLOAT_0_TO_1] [--conv-mask-to-poly]
```

Examples:

```bash
cvat-cli --profile prod task auto-annotate 42 \
  --function-module cvat_sdk.auto_annotation.functions.torchvision_detection \
  -p model_name=str:fasterrcnn_resnet50_fpn_v2 \
  -p box_score_thresh=float:0.5

cvat-cli --profile prod task auto-annotate 42 --function-file path/to/my_func.py \
  --clear-existing --conf-threshold 0.4 --conv-mask-to-poly
```

Parameter values use `NAME=TYPE:VALUE`; supported types are `int`, `float`, `str`, and `bool`. The CLI does not add local directories to `PYTHONPATH`; set `PYTHONPATH` explicitly when a function file/module imports sibling modules. For function protocol details, route to `../../auto-annotation/SKILL.md`.

## Project commands

### `project ls`

```bash
cvat-cli --profile prod project ls
cvat-cli --profile prod project ls --json > projects.json
```

Without `--json`, the command prints project IDs.

### `project create`

```bash
cvat-cli --profile prod project create "vehicle project" --labels labels.json
cvat-cli --profile prod project create "COCO project" \
  --dataset_path coco.zip --dataset_format "COCO 1.0" --completion_verification_period 1
```

Options include `--labels`, `--bug_tracker`/`--bug`, `--dataset_path`, `--dataset_format` (default `CVAT 1.1`), and `--completion_verification_period` (default `2`). The command prints the new project ID on success.

### Project dataset import/export and backups

```bash
cvat-cli --profile prod project export-dataset --format "CVAT for images 1.1" 7 project-7.zip
cvat-cli --profile prod project export-dataset --format "COCO 1.0" --with-images yes 7 project-7-coco.zip
cvat-cli --profile prod project import-dataset --format "COCO 1.0" 7 coco.zip
cvat-cli --profile prod project backup 7 project-7-backup.zip
cvat-cli --profile prod project create-from-backup project-7-backup.zip
```

Project import creates tasks in the project from a dataset, including images and annotations. It requires labels compatible with the incoming dataset.

## Native function commands

Native function commands are available for CVAT Enterprise/Cloud only and use the same AA function loading flags as `task auto-annotate`.

```bash
# Create a native function; success prints the function ID.
cvat-cli --profile prod function create-native "Faster R-CNN" \
  --visibility private \
  --function-module cvat_sdk.auto_annotation.functions.torchvision_detection \
  -p model_name=str:fasterrcnn_resnet50_fpn_v2

# Process queued annotation requests until interrupted.
cvat-cli --profile prod function run-agent 123 \
  --function-module cvat_sdk.auto_annotation.functions.torchvision_detection \
  -p model_name=str:fasterrcnn_resnet50_fpn_v2

# Drain pending work once and exit.
cvat-cli --profile prod function run-agent 123 --burst --function-file path/to/function.py

# Delete function metadata.
cvat-cli --profile prod function delete 123
```

`create-native` accepts `--visibility private|public` and prints the function ID. `run-agent` has long-running behavior unless `--burst` is supplied. The agent uses a temporary local dataset cache while running.

## JSON output and scripting

Only list commands expose built-in JSON output:

```bash
cvat-cli --profile prod task ls --json > tasks.json
cvat-cli --profile prod project ls --json > projects.json
```

Typical validation patterns:

```bash
# Fail when a named task is missing.
jq -e '.results[] | select(.name == "vehicle task") | .id' tasks.json

# Capture a newly created ID from stdout.
task_id=$(cvat-cli --profile prod task create "vehicle task" --labels labels.json local img1.jpg img2.jpg)
printf 'created task %s\n' "$task_id"
```

For machine-readable lifecycle automation, capture command stdout/stderr separately, parse only documented stdout values such as IDs and JSON, and redact stderr before saving debug logs.

## Command ownership cross-links

- Python SDK equivalents and low-level API fallback: `../../sdk-automation/SKILL.md`.
- Dataset format selection, manifests, cloud/local/share data-flow caveats, and PyTorch datasets: `../../dataset-ops/SKILL.md`.
- Auto-annotation function implementation and protocol validation: `../../auto-annotation/SKILL.md`.
- Server deployment, self-hosted URL/port configuration, TLS, and service health: `../../deployment-admin/SKILL.md`.
