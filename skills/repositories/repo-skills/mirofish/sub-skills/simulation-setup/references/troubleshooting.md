# Simulation setup troubleshooting

Use this matrix for Step 2 preparation failures and ambiguous setup states. Runtime start/stop/interview problems belong to `simulation-run`.

## Fast triage order

1. Read `GET /api/simulation/<simulation_id>` for `status`, `profiles_generated`, `config_generated`, counts, platform flags, and `error`.
2. Read `POST /api/simulation/prepare/status` with both `task_id` and `simulation_id` if you have both.
3. Read `GET /api/simulation/<simulation_id>/profiles/realtime?platform=reddit` and/or `platform=twitter` for partial profile data and `total_expected`.
4. Read `GET /api/simulation/<simulation_id>/config/realtime` for `generation_stage`, `profiles_generated`, `config_generated`, parse status, and config summary.
5. If entity filtering may be the cause, inspect `GET /api/simulation/entities/<graph_id>?enrich=false` before regenerating.

## Matrix

| Symptom | Likely cause | What to inspect | Fix |
|---|---|---|---|
| `/prepare` returns 400 for missing `simulation_id` | Caller did not create or pass simulation id | Request body | Call `/api/simulation/create` first or use the correct `sim_...` id. |
| `/prepare` returns project missing requirement | Project lacks `simulation_requirement` | Project data and create/upload flow | Return to graph/project creation and supply a non-empty simulation requirement. Setup config generation depends on it. |
| Entity endpoints fail with Zep key error | `ZEP_API_KEY` not configured | Backend environment validation | Configure `ZEP_API_KEY`. Do not set unsupported `ZEP_API_URL`; this app is wired for Zep Cloud. |
| Setup task fails with "No matching entities found" / `没有找到符合条件的实体` | Graph nodes only have default labels, filter is too narrow, wrong graph id, or graph build did not use usable ontology labels | `GET /entities/<graph_id>?enrich=false`; inspect `filtered_count`, `entity_types`, sample `labels` | Remove `entity_types`, use exact labels from `entity_types`, or rebuild/fix the graph ontology via `graph-build`. Then call `/prepare` with `force_regenerate: true`. |
| `filtered_count` positive with no filter but zero after filter | Entity type spelling/case mismatch | `data.entity_types` from entity endpoint | Use exact custom labels, e.g. `MediaOutlet` not `mediaoutlet`. |
| Entity detail lacks incoming edges | Caller used a read path without full graph context | Entity detail endpoint and edge enrichment setting | Prefer entity list/detail endpoints that pass graph id and use full graph edge pagination; use `enrich=true` when preparing profiles. |
| `/prepare/status` says `not_started` after backend restart | Task manager is in-memory; task id was lost | `GET /config/realtime`, `GET /profiles/realtime`, `GET /<simulation_id>` | If artifacts are complete, use them. If not, restart preparation. If partial files remain and no task is active, use `force_regenerate: true`. |
| `/prepare` returns `already_prepared: true` but state was `preparing` | Files and `config_generated` prove completion | `prepare_info.status`, `state.json` status | Accept it. The backend updates `preparing` to `ready` during the ready check. |
| `/prepare` keeps starting new work for a single-platform simulation | Prepared-artifact reuse check currently requires both `reddit_profiles.json` and `twitter_profiles.csv` | Platform flags, existing profile files, `prepare_info.missing_files` if available | Prefer dual-platform create for the UI path. For intentional single-platform setup, validate the enabled profile file and config directly; avoid relying solely on `already_prepared`. |
| Realtime profiles return empty list while task is processing | Profile file is not created yet or is being rewritten | `file_exists`, `file_modified_at`, `is_generating`, task `progress_detail` | Keep polling. Do not mark failed unless task/status is failed or no progress occurs beyond a reasonable generation window. |
| Realtime config returns `config: null` with `file_exists: true` | JSON is being written or partial/corrupt | `is_generating`, `status`, `error`, `config_generated` | Keep polling while generating. If `status: failed` or generation stopped, regenerate after preserving useful error context. |
| `config_generated: true` but `/config/download` is 404 | Config file is missing despite state flag | `GET /config/realtime` and server-side artifact existence if available | Treat as partial/stale setup. Run `/prepare` with `force_regenerate: true` after checking graph/entity readiness. |
| `profiles_generated: true` but one profile endpoint has `file_exists: false` | Platform disabled, write failure, or single-platform caveat | Simulation platform flags and realtime endpoints for both platforms | If platform was disabled, validate only enabled platform for runtime but note reuse caveat. If platform enabled, regenerate. |
| `/profiles?platform=...` returns platform error | Invalid completed-profile platform | Exact query value | Use lowercase `reddit` or `twitter`. Do not pass `parallel` to setup profile endpoints. |
| `/profiles/realtime?platform=bad` appears to read Twitter CSV | Realtime implementation treats non-`reddit` as Twitter branch | Query value | Use exact `reddit` or `twitter`; do not infer a third platform from this behavior. |
| `/generate-profiles` with unknown platform returns unexpected keys | Standalone generator returns generic dict for unknown platform | Response `data.platform` and profile keys | Use `reddit` or `twitter` when you need platform-specific data. Unknown platform output is inspection-only. |
| Initial posts fail later because agent id is missing | Config `poster_agent_id` was not assigned to an existing agent | `event_config.initial_posts`, `agent_configs[*].agent_id` | Regenerate config, or manually repair only if you fully understand the event config. Ensure each poster id exists. |
| Agents per hour exceeds agent count or rounds look odd | LLM generated unrealistic time config, then parser corrected some fields | `time_config` and computed rounds | Accept parser corrections if valid. If scenario is wrong, regenerate setup with better simulation requirement/source docs rather than editing runtime state blindly. |
| Missing script download or unknown script | Requested launcher name is not in the allowed list | Download URL | Use one of the backend-managed launcher names exposed by the API, or the bundled `action_logger.py` helper for safe local smoke checks. |
| User returned from Step 3 and Step 2 sees live env | Runtime environment remained alive for interviews | `POST /env-status` | Try `POST /close-env` for graceful close. If close fails or process is running/stuck, route to `simulation-run` for stop/restart handling. |

## Zero-entity recovery workflow

1. Call `GET /api/simulation/entities/<graph_id>?enrich=false` with no `entity_types`.
2. If `filtered_count` is zero, inspect graph/ontology through `graph-build`; setup cannot invent custom labels.
3. If `filtered_count` is positive, copy exact values from `entity_types` into your `/prepare` request.
4. If the previous prepare failed, call `/prepare` again with `force_regenerate: true` after the entity issue is fixed.
5. Watch `/prepare/status`, `/profiles/realtime`, and `/config/realtime` until ready.

## Stale or partial setup recovery workflow

1. Preserve the current error message, `status`, and which files/endpoints are missing.
2. Decide if the graph and entity filters are still correct. If not, fix those first.
3. If a task is actively `processing`, wait unless realtime endpoints show terminal failure.
4. If no task is active and files are partial, call `/prepare` with `force_regenerate: true`.
5. Revalidate profile file shape and config skeleton before handing off to `simulation-run`.

## Required keys and environment reminders

- `ZEP_API_KEY` is required for entity reads and profile context enrichment.
- `LLM_API_KEY` is required for profile/config generators even when some profile generation later falls back internally.
- `LLM_BASE_URL` defaults to the OpenAI-compatible endpoint if unset.
- `LLM_MODEL_NAME` defaults to `gpt-4o-mini` if unset.
- `project_id`, `graph_id`, `simulation_id`, and `task_id` are different identifiers. Do not substitute one for another.
- `simulation_requirement` lives on the project and is required by `/prepare`.

## When to stop and reroute

- Need to build, reset, or delete a graph: use `graph-build`.
- Need to start/restart/stop runtime or inspect action timelines: use `simulation-run`.
- Need to interview agents or close a live wait-mode environment after runtime: use `simulation-run`.
- Need to generate or inspect reports: use `reporting`.
