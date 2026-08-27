# Simulation setup API reference

All paths below are relative to the backend host. The Flask blueprint prefix is `/api/simulation`.

Response envelopes usually use:

```json
{"success": true, "data": {}}
```

Failures usually use:

```json
{"success": false, "error": "..."}
```

Some 500 responses include `traceback`; do not expose it to end users unless you are debugging locally.

## Entity endpoints

### `GET /api/simulation/entities/<graph_id>`

Read all simulation-usable entities from a graph.

Query parameters:

| Name | Type | Default | Meaning |
|---|---:|---:|---|
| `entity_types` | comma-separated strings | none | Keep only nodes with matching custom labels, for example `Student,MediaOutlet`. Exact label match is required. |
| `enrich` | `true`/`false` | `true` | Include related edge facts and related node summaries. Use `false` for fast count/label preview. |

Success data:

```json
{
  "entities": [
    {
      "uuid": "node_uuid",
      "name": "Alice",
      "labels": ["Entity", "Student"],
      "summary": "...",
      "attributes": {},
      "related_edges": [
        {"direction": "outgoing", "edge_name": "KNOWS", "fact": "Alice knows Bob", "target_node_uuid": "..."}
      ],
      "related_nodes": [
        {"uuid": "...", "name": "Bob", "labels": ["Entity", "Student"], "summary": "..."}
      ]
    }
  ],
  "entity_types": ["Student"],
  "total_count": 12,
  "filtered_count": 1
}
```

Filtering rule: a node is eligible only when labels contain at least one label other than `Entity` or `Node`. With `entity_types`, at least one custom label must exactly match the requested type.

### `GET /api/simulation/entities/<graph_id>/<entity_uuid>`

Read one entity with complete context. Returns 404 if the node is not found. Authentication, permission, transport, and non-404 Zep failures are propagated as errors rather than converted to empty context.

### `GET /api/simulation/entities/<graph_id>/by-type/<entity_type>`

Shortcut for the same filter with one exact entity type. Query parameter `enrich` behaves as above. Success data contains `entity_type`, `count`, and `entities`.

## Simulation record endpoints

### `POST /api/simulation/create`

Create a persisted simulation state.

Request:

```json
{
  "project_id": "proj_...",
  "graph_id": "mirofish_...",
  "enable_twitter": true,
  "enable_reddit": true
}
```

Fields:

| Field | Required | Default | Meaning |
|---|---:|---:|---|
| `project_id` | yes | none | Project containing the graph and simulation requirement. |
| `graph_id` | no | project `graph_id` | Graph to read during setup. |
| `enable_twitter` | no | `true` | Generate Twitter config/profile file and allow Twitter runtime. |
| `enable_reddit` | no | `true` | Generate Reddit config/profile file and allow Reddit runtime. |

Success data is the full `SimulationState`: `simulation_id`, `project_id`, `graph_id`, platform booleans, `status`, counts, generation flags, timestamps, and `error`.

Common failures:

- 400: missing `project_id`.
- 404: project not found.
- 400: no graph has been built for the project and no `graph_id` was supplied.

### `GET /api/simulation/<simulation_id>`

Read a persisted simulation state. If state is `ready`, the response also includes `run_instructions` with the config file, backend scripts directory, and sample Python run commands. Use those only as setup handoff data; runtime execution belongs to `simulation-run`.

### `GET /api/simulation/list`

List simulations. Optional query `project_id=<project_id>` filters by project.

### `GET /api/simulation/history`

List recent simulations enriched for the home/history UI. Query `limit` defaults to 20. It includes project name/files, `simulation_requirement` from config if present, counts, current/total rounds if runtime state exists, latest report id, and display date fields. It is a convenience/history endpoint, not the primary setup control path.

## Preparation endpoints

### `POST /api/simulation/prepare`

Start or reuse setup preparation.

Request:

```json
{
  "simulation_id": "sim_...",
  "entity_types": ["Student", "MediaOutlet"],
  "use_llm_for_profiles": true,
  "parallel_profile_count": 5,
  "force_regenerate": false
}
```

Fields:

| Field | Required | Default | Meaning |
|---|---:|---:|---|
| `simulation_id` | yes | none | Simulation record created by `/create`. |
| `entity_types` | no | all custom-labeled entities | Restrict graph entities by exact labels. |
| `use_llm_for_profiles` | no | `true` | Use the LLM profile generator; false uses rule-based fallback. |
| `parallel_profile_count` | no | `5` | Thread-pool worker count for profile generation. |
| `force_regenerate` | no | `false` | Ignore existing artifacts and rebuild profiles/config. |

If artifacts are already considered prepared and `force_regenerate` is false, success data is:

```json
{
  "simulation_id": "sim_...",
  "status": "ready",
  "message": "Preparation already complete. No need to regenerate.",
  "already_prepared": true,
  "prepare_info": {
    "status": "ready",
    "entities_count": 10,
    "profiles_count": 10,
    "entity_types": ["Student"],
    "config_generated": true,
    "existing_files": ["state.json", "simulation_config.json", "reddit_profiles.json", "twitter_profiles.csv"]
  }
}
```

For a new background task, success data is:

```json
{
  "simulation_id": "sim_...",
  "task_id": "uuid-task-id",
  "status": "preparing",
  "message": "Prepare task started",
  "already_prepared": false,
  "expected_entities_count": 10,
  "entity_types": ["Student", "MediaOutlet"]
}
```

Immediate failures include missing `simulation_id`, missing simulation, missing project, and missing project `simulation_requirement`. Zero matching entities is usually recorded by the background task as a failed task and failed simulation state.

### `POST /api/simulation/prepare/status`

Poll setup status by `task_id`, by `simulation_id`, or both.

Request:

```json
{"task_id": "uuid-task-id", "simulation_id": "sim_..."}
```

Behavior:

- If `simulation_id` is present, the backend first checks persisted artifacts. If they satisfy the ready check, response is `status: "ready"`, `progress: 100`, and `already_prepared: true` even if the task id is old or missing.
- If no task id is present and ready artifacts are not found, response is success with `status: "not_started"`, `progress: 0`, and `already_prepared: false`.
- If a supplied task id is not found and ready artifacts are not found, response is 404.
- Otherwise response is the in-memory task dictionary with `already_prepared: false`.

Task dictionary shape:

```json
{
  "task_id": "uuid-task-id",
  "task_type": "simulation_prepare",
  "status": "pending|processing|completed|failed",
  "created_at": "ISO time",
  "updated_at": "ISO time",
  "progress": 45,
  "message": "[2/4] Generating Agent Profiles: 3/10 - ...",
  "progress_detail": {
    "current_stage": "generating_profiles",
    "current_stage_name": "Generating Agent Profiles",
    "stage_index": 2,
    "total_stages": 4,
    "stage_progress": 50,
    "current_item": 3,
    "total_items": 10,
    "item_description": "..."
  },
  "result": {},
  "error": null,
  "metadata": {"simulation_id": "sim_...", "project_id": "proj_..."}
}
```

## Profile endpoints

### `GET /api/simulation/<simulation_id>/profiles`

Read completed profile data through `SimulationManager.get_profiles`.

Query:

| Name | Type | Default |
|---|---|---|
| `platform` | `reddit` or `twitter` | derived from simulation platform flags |

Default platform selection:

- both Twitter and Reddit enabled: `reddit`
- Twitter only: `twitter`
- Reddit only or neither: `reddit`

Success data:

```json
{"platform": "reddit", "count": 10, "profiles": [{"user_id": 0, "username": "alice_123"}]}
```

Invalid completed-profile platform values are rejected with a ValueError response. Use exact lowercase `reddit` or `twitter`.

### `GET /api/simulation/<simulation_id>/profiles/realtime`

Read profile files directly during generation. Query `platform` has the same intended values and default selection. The implementation treats `reddit` specially and uses the Twitter CSV branch for any other value, so pass exact valid platform strings.

Success data:

```json
{
  "simulation_id": "sim_...",
  "platform": "reddit",
  "count": 4,
  "total_expected": 10,
  "is_generating": true,
  "status": "preparing",
  "error": null,
  "file_exists": true,
  "file_modified_at": "ISO time",
  "profiles": []
}
```

If the file is being rewritten and cannot be parsed, this endpoint logs a warning and returns an empty `profiles` list instead of failing.

### `POST /api/simulation/generate-profiles`

Generate profiles directly from a graph without creating or preparing a simulation. It returns profile data in the response and does not save a simulation directory.

Request:

```json
{
  "graph_id": "mirofish_...",
  "entity_types": ["Student"],
  "use_llm": true,
  "platform": "reddit"
}
```

Behavior:

- Missing `graph_id` returns 400.
- Entity filtering uses `enrich_with_edges: true`.
- Zero filtered entities returns 400 with "No matching entities found".
- `platform: "reddit"` returns Reddit-format JSON objects.
- `platform: "twitter"` returns Twitter-format JSON objects, not the stored CSV file format.
- Any other platform string returns the generator's full generic dictionary format rather than a platform-specific OASIS runtime file shape.

## Config endpoints

### `GET /api/simulation/<simulation_id>/config`

Read completed `simulation_config.json` through the manager. Returns 404 if the config file is not found.

### `GET /api/simulation/<simulation_id>/config/realtime`

Read `simulation_config.json` directly during generation.

Success data includes:

```json
{
  "simulation_id": "sim_...",
  "file_exists": true,
  "file_modified_at": "ISO time",
  "is_generating": false,
  "status": "ready",
  "error": null,
  "generation_stage": "completed",
  "profiles_generated": true,
  "config_generated": true,
  "config": {},
  "summary": {
    "total_agents": 10,
    "simulation_hours": 72,
    "initial_posts_count": 3,
    "hot_topics_count": 5,
    "has_twitter_config": true,
    "has_reddit_config": true,
    "generated_at": "ISO time",
    "llm_model": "gpt-4o-mini"
  }
}
```

Generation stage is inferred from `state.json`:

- `generating_profiles` when status is `preparing` and `profiles_generated` is false.
- `generating_config` when status is `preparing` and `profiles_generated` is true.
- `completed` when status is `ready`.
- `failed` when status is `failed`.

During a partial write, parse failure returns `config: null` rather than failing the endpoint.

### `GET /api/simulation/<simulation_id>/config/download`

Download `simulation_config.json` as an attachment. Returns 404 if the file does not exist.

## Script download endpoint

### `GET /api/simulation/script/<script_name>/download`

Download one generic run helper from the backend scripts area. The backend exposes launcher downloads for the supported run modes plus the bundled `action_logger.py` helper.

Unknown script names return 400. Missing files return 404. The scripts are not copied into the simulation directory by setup.

## Environment endpoints relevant to setup screens

These endpoints are mainly runtime/finalization operations, but Step 2 uses them when a user navigates back from Step 3 and a live environment may still be waiting for commands.

### `POST /api/simulation/env-status`

Request: `{"simulation_id":"sim_..."}`. Returns `env_alive`, `twitter_available`, `reddit_available`, and a user-facing message. Use before deciding whether a previous runtime environment needs graceful close.

### `POST /api/simulation/close-env`

Request: `{"simulation_id":"sim_...", "timeout":30}`. Sends a graceful close command to a live wait-mode environment and updates simulation status to `completed` if a state exists. If graceful close fails or a process is actively running, use `simulation-run` for stop/restart decisions.

## Runtime endpoints deliberately excluded

`/start`, `/stop`, `/run-status`, `/run-status/detail`, `/actions`, `/timeline`, `/agent-stats`, `/posts`, `/comments`, and all `/interview*` endpoints belong to `simulation-run`, not this setup sub-skill.
