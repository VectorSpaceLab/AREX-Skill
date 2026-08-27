# Server API Reference

ComfyUI runs an `aiohttp` server. Most core routes are registered both at their legacy path and under an `/api` prefix, so `/prompt` and `/api/prompt` are equivalent for current core routes. Asset routes are already declared under `/api/assets` and should be used with that prefix.

## Queue and Execution Routes

### `POST /prompt`

Queues one API-format prompt graph.

Minimal body:

```json
{
  "prompt": {
    "3": {"class_type": "KSampler", "inputs": {}}
  },
  "client_id": "automation-client"
}
```

Useful fields:

- `prompt`: required API workflow object. Each node id maps to a node object with `class_type` and `inputs`.
- `client_id`: optional client/session id used by websocket progress routing.
- `prompt_id`: optional canonical lowercase hyphenated UUID. Omit it to let ComfyUI mint one. Non-canonical forms such as uppercase UUIDs, braced UUIDs, URNs, bare hex, or arbitrary labels are rejected.
- `front`: optional truthy value to queue at the front.
- `number`: optional queue ordering number.
- `partial_execution_targets`: optional advanced target list for partial execution.
- `extra_data`: optional metadata. For hosted Comfy API nodes, place `api_key_comfy_org` here from a secret source; do not embed secrets in workflow JSON.

Successful response:

```json
{"prompt_id": "a1b2c3d4-e5f6-7a89-b0c1-d2e3f4a5b6c7", "number": 0, "node_errors": {}}
```

Failure response uses `400` and includes an `error` object plus `node_errors` when validation fails.

### `GET /prompt`

Returns queue status summary from the prompt queue. Use `GET /queue` for explicit running/pending lists.

### `GET /queue`

Returns:

```json
{"queue_running": [...], "queue_pending": [...]}
```

Sensitive queue metadata is removed from queue item tuples before returning.

### `POST /queue`

Manages pending queue entries.

```json
{"clear": true}
```

or

```json
{"delete": ["<prompt_id>"]}
```

### `POST /interrupt`

Interrupts execution. Body may be empty for global interrupt, or targeted:

```json
{"prompt_id": "<currently-running-prompt-id>"}
```

Targeted interrupt only fires when the specified prompt is currently running.

### `POST /free`

Requests model unload and/or memory release flags:

```json
{"unload_models": true, "free_memory": true}
```

### `GET /history`

Returns prompt history. Query parameters:

- `max_items`: maximum count.
- `offset`: offset; default behavior uses `-1`.

### `GET /history/{prompt_id}`

Returns only the selected prompt history, usually shaped as:

```json
{
  "<prompt_id>": {
    "prompt": [/* queue tuple details */],
    "outputs": {
      "9": {
        "images": [
          {"filename": "ComfyUI_00001_.png", "subfolder": "", "type": "output"}
        ]
      }
    }
  }
}
```

### `POST /history`

Deletes history entries or clears history:

```json
{"clear": true}
```

or

```json
{"delete": ["<prompt_id>"]}
```

## Jobs Routes

The newer jobs surface wraps queue/history information with status, filtering, pagination, and cancel APIs.

- `GET /api/jobs`: list jobs. Query `status=pending,in_progress,completed,failed,cancelled`, `workflow_id=<id>`, `sort_by=created_at|execution_duration`, `sort_order=asc|desc`, `limit=<n>`, `offset=<n>`.
- `GET /api/jobs/{job_id}`: fetch one job.
- `POST /api/jobs/{job_id}/cancel`: idempotently cancel a running or pending job.
- `POST /api/jobs/cancel`: batch cancel with body `{"job_ids": ["<uuid>"]}`. Invalid ids produce `400`; already-finished or unknown ids are no-ops.

## Output and File Routes

### `GET /view`

Downloads or previews files from output/input/temp directories, or resolves `blake3:` asset hashes. Query parameters:

- `filename`: required file name or `blake3:<hash>` asset reference.
- `subfolder`: optional subfolder under the selected type.
- `type`: `output`, `input`, or `temp`; default is `output` when needed.
- `preview`: optional preview format such as `webp;90` or `jpeg;80`.
- `channel`: `rgb`, `a`, or default RGBA/file response.

ComfyUI rejects empty file names, absolute paths, and traversal attempts.

### `POST /upload/image`

Multipart upload for images into the input area. Common fields are `image`, optional `subfolder`, optional `type`, and optional `overwrite` depending on frontend behavior.

### `POST /upload/mask`

Multipart upload for mask data tied to `original_ref`. The route validates the original file reference and preserves image metadata where possible.

### `GET /view_metadata/{folder_name}`

Reads safetensors metadata for a model file. Requires `filename=<name>` and only responds for `.safetensors` files with `__metadata__`.

## Discovery and System Routes

- `GET /`: frontend `index.html`.
- `GET /ws?clientId=<client_id>`: websocket progress and status stream.
- `GET /embeddings`: embedding names without file extensions.
- `GET /models`: model folder categories.
- `GET /models/{folder}`: model file names for one category.
- `GET /experiment/models`: experimental richer model folder list excluding some internal folders.
- `GET /experiment/models/{folder}`: experimental richer model file list.
- `GET /experiment/models/preview/{folder}/{path_index}/{filename}`: model preview image when available.
- `GET /extensions`: frontend extension JavaScript files.
- `GET /system_stats`: system, Python, ComfyUI package, frontend/template, and device memory details.
- `GET /features`: server feature flags.
- `GET /object_info`: all loaded node metadata. Route node authoring details to `../../custom-nodes/`.
- `GET /object_info/{node_class}`: one loaded node’s metadata.
- `GET /workflow_templates`: built-in/custom workflow templates.
- `GET /i18n`: localization payloads.
- `GET /node_replacements`: node replacement metadata.
- `GET /global_subgraphs` and `GET /global_subgraphs/{id}`: global subgraph entries.

## Settings and User Data Routes

These operate on ComfyUI’s user directory and become especially important with `--multi-user`.

- `GET /users`: with `--multi-user`, returns server storage and users; without it, returns migration status for the default user area.
- `POST /users`: body `{"username": "name"}` creates a user id, rejecting duplicates and reserved system prefixes.
- `GET /settings`: user settings JSON.
- `GET /settings/{id}`: one setting value or `null`.
- `POST /settings`: merge posted settings into existing settings.
- `POST /settings/{id}`: set one setting value.
- `GET /userdata?dir=<dir>&recurse=true&full_info=true&split=true`: list files in user data.
- `GET /v2/userdata?path=<path>`: structured recursive user-data listing.
- `GET /userdata/{file}`: download a user-data file.
- `POST /userdata/{file}`: upload raw file content. Query `overwrite=false` prevents replacement; `full_info=true` returns file info.
- `DELETE /userdata/{file}`: delete a user-data file.
- `POST /userdata/{file}/move/{dest}`: move/rename a user-data file.

User-data routes reject invalid users and path traversal. Do not assume a single shared settings directory when `--multi-user` is enabled.

## Assets Routes

The assets system is gated by `--enable-assets`. When disabled, asset routes return `503 SERVICE_DISABLED`.

Important routes include:

- `HEAD /api/assets/hash/{hash}`: check whether a `blake3:<hex>` hash exists.
- `GET /api/assets`: list assets with filters such as tags, name, metadata, sorting, pagination, and cursors.
- `GET /api/assets/{id}`: get asset metadata by reference UUID.
- `GET /api/assets/{id}/content?disposition=attachment|inline`: stream asset content.
- `POST /api/assets/from-hash`: create an asset reference from an existing content hash.
- Upload, metadata, tag, and delete routes are also present under `/api/assets`; inspect the route definitions when building a dedicated asset manager because this surface is newer and feature-gated.

## Internal Routes

`/internal/*` is for the frontend and is not a stable external automation surface. Current routes include logs, terminal log subscription, folder paths, and input/output/temp file lists:

- `GET /internal/logs`
- `GET /internal/logs/raw`
- `PATCH /internal/logs/subscribe`
- `GET /internal/folder_paths`
- `GET /internal/files/{output|input|temp}`

Avoid depending on these for durable integrations.
