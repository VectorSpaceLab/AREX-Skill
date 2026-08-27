# Simulation setup workflows

This reference covers MiroFish Step 2: turning a completed Zep graph into setup artifacts that the OASIS runtime can consume. It intentionally stops before `/api/simulation/start`; runtime execution belongs to `simulation-run`.

## Preconditions

Have these before setup work:

- Backend is reachable, for example `GET /health` returns an OK service response.
- A completed graph exists for the project: `project_id`, `graph_id`, and graph data can be read.
- The project has a non-empty `simulation_requirement`; setup refuses to prepare without it.
- `ZEP_API_KEY` is configured for entity reads, and `LLM_API_KEY`/`LLM_BASE_URL`/`LLM_MODEL_NAME` are configured for persona and config generation.
- Decide whether to keep the UI default dual-platform setup (`enable_twitter: true`, `enable_reddit: true`) or intentionally create a single-platform simulation. Dual platform is the most exercised path.

Use placeholders consistently in examples:

```bash
BASE_URL=http://localhost:5000
PROJECT_ID=proj_...
GRAPH_ID=mirofish_...
SIMULATION_ID=sim_...
TASK_ID=...
```

## 1. Create the simulation record

The front-end Step 1 button creates a simulation before navigating into Step 2. The backend stores a `state.json` under the configured simulation data directory and returns the new `simulation_id`.

```bash
curl -sS -X POST "$BASE_URL/api/simulation/create" \
  -H 'Content-Type: application/json' \
  -d '{
    "project_id": "'"$PROJECT_ID"'",
    "graph_id": "'"$GRAPH_ID"'",
    "enable_twitter": true,
    "enable_reddit": true
  }'
```

Expected success data contains:

```json
{
  "simulation_id": "sim_...",
  "project_id": "proj_...",
  "graph_id": "mirofish_...",
  "enable_twitter": true,
  "enable_reddit": true,
  "status": "created",
  "entities_count": 0,
  "profiles_count": 0,
  "profiles_generated": false,
  "config_generated": false
}
```

Create fails if `project_id` is missing, the project is not found, or no `graph_id` is available from either the request or project.

## 2. Inspect and filter entities before expensive generation

Entity filtering keeps graph nodes whose labels include at least one custom label beyond the default `Entity`/`Node` labels. If you do not know the available types, inspect without filters first:

```bash
curl -sS "$BASE_URL/api/simulation/entities/$GRAPH_ID?enrich=false"
```

Read `data.filtered_count`, `data.entity_types`, and a few `data.entities[*].labels`. If `filtered_count` is zero, the graph is not ready for simulation even if graph build completed: the ontology or graph nodes do not expose simulation-usable custom labels.

To narrow setup to selected types, use exact label strings:

```bash
curl -sS "$BASE_URL/api/simulation/entities/$GRAPH_ID?entity_types=Student,MediaOutlet&enrich=true"
curl -sS "$BASE_URL/api/simulation/entities/$GRAPH_ID/by-type/Student?enrich=true"
curl -sS "$BASE_URL/api/simulation/entities/$GRAPH_ID/<entity_uuid>"
```

Use `enrich=false` for a fast count and label preview. Use `enrich=true` when profile generation needs related edge facts and related nodes.

## 3. Start preparation

Preparation is asynchronous. The API returns quickly with a `task_id`; a background thread performs entity reads, profile generation, and config generation.

```bash
curl -sS -X POST "$BASE_URL/api/simulation/prepare" \
  -H 'Content-Type: application/json' \
  -d '{
    "simulation_id": "'"$SIMULATION_ID"'",
    "entity_types": ["Student", "MediaOutlet"],
    "use_llm_for_profiles": true,
    "parallel_profile_count": 5,
    "force_regenerate": false
  }'
```

Request fields:

- `simulation_id` is required.
- `entity_types` is optional. Omit it to use every graph node with a custom entity label.
- `use_llm_for_profiles` defaults to `true`; false falls back to rule-based personas.
- `parallel_profile_count` defaults to 5 in the API and controls parallel profile generation workers.
- `force_regenerate` defaults to `false`; set true only after deciding existing setup artifacts are stale or invalid.

Preparation sequence and progress stages:

1. `reading` (`0-20%`): read/filter graph nodes and optionally edges.
2. `generating_profiles` (`20-70%`): build `OasisAgentProfile` objects and write the realtime profile file for the preferred enabled platform.
3. `generating_config` (`70-90%`): generate `simulation_config.json` using the project requirement, extracted document text, filtered entities, and enabled platform flags.
4. `copying_scripts` (`90-100%`): legacy progress label; current run scripts remain in the backend scripts area and are not copied into the simulation directory.

If no matching entities are found in the background prepare, `state.json` is persisted with `status: "failed"`, `profiles_generated: false`, `config_generated: false`, an empty `config_reasoning`, and an explanatory error.

## 4. Poll task and realtime artifacts

Poll preparation status with both identifiers when possible:

```bash
curl -sS -X POST "$BASE_URL/api/simulation/prepare/status" \
  -H 'Content-Type: application/json' \
  -d '{"task_id":"'"$TASK_ID"'", "simulation_id":"'"$SIMULATION_ID"'"}'
```

Important response patterns:

- `status: "processing"` with `progress` and `progress_detail`: task is active.
- `status: "completed"`: the in-memory task finished; inspect `result` for simplified simulation state.
- `status: "ready"`, `already_prepared: true`, `progress: 100`: persisted artifacts satisfy the backend ready check.
- `status: "not_started"`, `already_prepared: false`: no task was supplied and ready artifacts were not detected.
- `status: "failed"`: read `error` and `state.json`/realtime endpoints before retrying.

Poll profiles during generation:

```bash
curl -sS "$BASE_URL/api/simulation/$SIMULATION_ID/profiles/realtime?platform=reddit"
curl -sS "$BASE_URL/api/simulation/$SIMULATION_ID/profiles/realtime?platform=twitter"
```

The realtime profile endpoint reads the profile file directly and can return partial lists while generation is still running. It returns `file_exists`, `file_modified_at`, `count`, `total_expected`, `is_generating`, `status`, `error`, and `profiles`.

Poll config during generation:

```bash
curl -sS "$BASE_URL/api/simulation/$SIMULATION_ID/config/realtime"
```

The realtime config endpoint returns `file_exists`, `file_modified_at`, `is_generating`, `generation_stage`, `profiles_generated`, `config_generated`, `status`, `error`, and `config`. When config is parseable it also returns `summary` with total agents, simulation hours, initial post count, hot-topic count, enabled platform config flags, generation time, and LLM model.

During a write, a realtime endpoint may temporarily return an empty profile list or `config: null` because JSON/CSV is being rewritten. Keep polling unless `status` is `failed` or the task failed.

## 5. Reuse versus regenerate

Before starting a new background task, `/prepare` checks for existing completed artifacts unless `force_regenerate` is true.

A persisted setup is considered prepared when all of these are true:

- Simulation directory exists.
- `state.json`, `simulation_config.json`, `reddit_profiles.json`, and `twitter_profiles.csv` exist.
- `state.json.config_generated` is true.
- `state.json.status` is one of `ready`, `preparing`, `running`, `completed`, `stopped`, or `failed`.

If the stored status is `preparing` but files and `config_generated` prove completion, the check updates status to `ready`.

Caveat: this ready check is dual-platform-biased because it requires both profile files. A single-platform simulation can be functionally prepared for its enabled platform while later reuse checks still report missing files. Prefer dual platform unless single-platform behavior is intentional, and validate single-platform readiness with the direct profile/config endpoints plus the simulation state.

Use `force_regenerate: true` when:

- Entity filters were wrong and generated the wrong agent set.
- The graph was rebuilt or reset after the simulation was created.
- Profiles/config are partial or stale and the task is no longer active.
- The setup failed and you have fixed the root cause.

Do not use `force_regenerate` just to start a simulation again; runtime restart and log cleanup belong to `simulation-run`.

## 6. Validate setup artifacts

A simulation is ready for `simulation-run` when these checks pass:

1. `GET /api/simulation/<simulation_id>` returns `status: "ready"` or a later state that still has completed setup artifacts.
2. Realtime config shows `config_generated: true` and a non-null `config`.
3. Realtime profiles for each enabled platform report `file_exists: true` and `count > 0`.
4. Stored profile count and `len(config.agent_configs)` match the intended agent count.
5. Every `agent_configs[*].agent_id` is unique, starts at zero, and corresponds to one generated profile row/object.
6. Every `event_config.initial_posts[*].poster_agent_id` is an integer present in `agent_configs`.
7. `twitter_config` exists if Twitter is enabled; `reddit_config` exists if Reddit is enabled.
8. Time config can produce positive rounds: `floor(total_simulation_hours * 60 / minutes_per_round) > 0`.

For a local profile-file preflight independent of MiroFish imports, run:

```bash
python scripts/profile-format-smoke.py --self-test
```

## 7. Download setup artifacts and run scripts

Download the generated config:

```bash
curl -OJ "$BASE_URL/api/simulation/$SIMULATION_ID/config/download"
```

Download backend-managed launcher helpers by download name:

```bash
curl -OJ "$BASE_URL/api/simulation/script/<launcher-name>/download"
curl -OJ "$BASE_URL/api/simulation/script/action_logger.py/download"
```

The backend chooses the launcher name for the selected mode. `action_logger.py` is the bundled helper that is safe to copy/adapt into this skill.

There is no dedicated profile-file download endpoint. Use `GET /profiles` or `GET /profiles/realtime` for API-visible profile data, or inspect the server-side simulation data directory if operating on the backend host.

## 8. Handoff to runtime

After setup validation, stop using this sub-skill for runtime actions. Hand off to `simulation-run` with:

- `simulation_id`
- enabled platforms
- whether setup used custom `entity_types`
- total profiles/agents
- computed recommended rounds from `time_config`
- whether any single-platform or reuse-check caveat remains unresolved
