# CVAT CLI workflows

Use these patterns as starting points for future automation. They assume `cvat-cli` is installed and a CVAT server is reachable.

## Credential-safe setup

### Preferred: saved PAT profile

```bash
# Prompt securely for the PAT and save the profile.
cvat-cli --server-host https://app.cvat.ai profile create --name prod --set-default

# Confirm profile visibility without printing token values.
cvat-cli profile list
cvat-cli profile default

# Use it.
cvat-cli --profile prod task ls
```

Do not paste the token into a shared shell transcript. If importing from a token file, delete or protect the source token file after the profile is saved. Profile deletion does not revoke the token server-side.

### Non-profile automation with environment variables

```bash
# In a secret manager, CI secret, or local protected shell only:
export CVAT_ACCESS_TOKEN="..."

# Server remains explicit; token value is not in the command line.
cvat-cli --server-host https://app.cvat.ai --org team task ls --json > tasks.json
```

When password auth is unavoidable:

```bash
# Avoid USER:PASS in the command. Set PASS in a protected environment or allow prompt input.
export PASS="..."
cvat-cli --server-host https://cvat.example.org --auth annotator --org team task ls
unset PASS
```

## Idempotent task creation with validation

```bash
set -euo pipefail
profile=prod
org=team
name="vehicle review"
labels=labels.json

# Validate local inputs first.
test -s "$labels"
test -f images/img001.jpg
python -m json.tool "$labels" >/dev/null

# Query existing tasks as JSON and reuse by exact name if present.
cvat-cli --profile "$profile" --org "$org" task ls --json > tasks.json
existing_id=$(jq -r --arg name "$name" '.results[]? | select(.name == $name) | .id' tasks.json | head -n 1)

if [ -n "$existing_id" ]; then
  task_id="$existing_id"
else
  task_id=$(cvat-cli --profile "$profile" --org "$org" task create "$name" \
    --labels "$labels" --image_quality 75 local images/img001.jpg images/img002.jpg)
fi

printf 'task_id=%s\n' "$task_id"
cvat-cli --profile "$profile" --org "$org" task frames --outdir sanity-frames --quality compressed "$task_id" 0
```

Validation checkpoints:

- `task ls --json` exits 0 and has a `.results` array or equivalent page structure.
- `task create` prints one numeric ID on stdout.
- A frame sanity download writes files named like `task_<ID>_frame_000000.jpg`.

## Task creation variants

### Local files with inline labels

```bash
cvat-cli --profile prod task create "cats and dogs" \
  --labels '[{"name":"cat","attributes":[]},{"name":"dog","attributes":[]}]' \
  local cat1.jpg dog1.jpg
```

### Remote video in a project

```bash
cvat-cli --profile prod task create "remote video" --project_id 17 \
  --segment_size 100 --overlap 5 --start_frame 0 --stop_frame 1000 --frame_step 5 \
  remote https://example.org/video.mp4
```

### Shared/cloud storage manifest filtering

```bash
cvat-cli --profile prod task create "cloud subset" \
  --labels labels.json --use_cache --cloud_storage_id 3 --filename_pattern "images/*.jpg" \
  share manifest.jsonl
```

Use `--copy_data` only with `share` when the server should copy the shared resource into CVAT storage.

## Export, import, backup, and restore

### Export annotations

```bash
# Annotation-only export.
cvat-cli --profile prod task export-dataset --format "CVAT for images 1.1" 42 task-42-cvat.zip

# Include images only when the user wants a larger self-contained dataset artifact.
cvat-cli --profile prod task export-dataset --format "COCO 1.0" --with-images yes 42 task-42-coco-with-images.zip

# Project export has the same generic options.
cvat-cli --profile prod project export-dataset --format "COCO 1.0" --with-images no 7 project-7-coco.zip
```

### Import annotations or create project tasks from a dataset

```bash
# Existing task: import annotations only.
cvat-cli --profile prod task import-dataset --format "CVAT 1.1" 42 annotations.xml

# Existing project: create tasks from a dataset with images and annotations.
cvat-cli --profile prod project import-dataset --format "COCO 1.0" 7 coco.zip
```

If label compatibility or format choice is unclear, route to `../../dataset-ops/SKILL.md` before running the import.

### Backup before destructive changes

```bash
cvat-cli --profile prod task backup --completion_verification_period 5 42 backups/task-42.zip
cvat-cli --profile prod project backup --completion_verification_period 5 7 backups/project-7.zip
```

Restore into a new resource:

```bash
new_task_id=$(cvat-cli --profile prod task create-from-backup backups/task-42.zip)
new_project_id=$(cvat-cli --profile prod project create-from-backup backups/project-7.zip)
```

## Project lifecycle

```bash
project_id=$(cvat-cli --profile prod project create "road scene project" --labels labels.json)

cvat-cli --profile prod task create "road scene batch 1" --project_id "$project_id" local images/*.jpg
cvat-cli --profile prod project export-dataset --format "CVAT for images 1.1" "$project_id" road-scenes.zip

# Confirm before deletion.
cvat-cli --profile prod project ls --json | jq --arg id "$project_id" '.results[]? | select(.id == ($id|tonumber))'
cvat-cli --profile prod project delete "$project_id"
```

`project create --dataset_path DATASET --dataset_format FORMAT` can create a project and import a dataset in one command. Use `--completion_verification_period` to adjust background status polling.

## Local auto-annotation command

For local task annotation with a Python function:

```bash
# Function module available on Python path.
cvat-cli --profile prod task auto-annotate 42 \
  --function-module my_package.cvat_function \
  -p threshold=float:0.5 \
  --conf-threshold 0.5 \
  --conv-mask-to-poly

# Function file with local imports.
PYTHONPATH=path/to/project cvat-cli --profile prod task auto-annotate 42 \
  --function-file path/to/project/my_func.py --clear-existing
```

Constraints:

- Exactly one of `--function-module` or `--function-file` is required.
- `-p` values use `NAME=TYPE:VALUE`, where type is `int`, `float`, `str`, or `bool`.
- `--conf-threshold` must be in `[0, 1]`.
- `--clear-existing` removes existing task annotations before uploading the generated result.
- `--allow-unmatched-labels` relaxes task/function label matching; use deliberately because it can hide mismatched taxonomy.
- The CLI does not add local paths to `PYTHONPATH`.

For function code, protocol shape, labels, masks, and model dependencies, route to `../../auto-annotation/SKILL.md`.

## Native function create/run-agent flow

Native functions let a CVAT Enterprise/Cloud server request work from an external local agent process.

```bash
function_id=$(cvat-cli --profile prod function create-native "Faster R-CNN" \
  --visibility private \
  --function-module cvat_sdk.auto_annotation.functions.torchvision_detection \
  -p model_name=str:fasterrcnn_resnet50_fpn_v2)

# Long-running worker; run under a supervisor for production use.
cvat-cli --profile prod function run-agent "$function_id" \
  --function-module cvat_sdk.auto_annotation.functions.torchvision_detection \
  -p model_name=str:fasterrcnn_resnet50_fpn_v2

# CI/smoke variant: drain available requests once and exit.
cvat-cli --profile prod function run-agent "$function_id" --burst \
  --function-module cvat_sdk.auto_annotation.functions.torchvision_detection \
  -p model_name=str:fasterrcnn_resnet50_fpn_v2
```

Validation signals:

- `create-native` prints one function ID.
- `run-agent` logs queue acquisition, progress updates, retry/backoff events, and completion/failure of annotation requests.
- A provider/kind mismatch means the function registered on the server is not compatible with the local function object.

## Using the bundled command builder

Generate commands without executing them:

```bash
python scripts/cvat_cli_command_builder.py --profile prod --org team task-create "demo" \
  --labels labels.json local img1.jpg img2.jpg

python scripts/cvat_cli_command_builder.py --profile prod task-export-dataset 42 task-42.zip \
  --format "COCO 1.0" --with-images yes

python scripts/cvat_cli_command_builder.py --server-host https://app.cvat.ai --require-token-env task-ls --json
```

The builder refuses unsafe credential arguments and enforces the `--profile` mutual-exclusion rule before printing a quoted shell command.
