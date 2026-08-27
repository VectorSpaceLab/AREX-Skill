---
name: simulation-setup
description: "Create and prepare MiroFish simulation setup artifacts from a
  completed Zep graph, including entity filtering, OASIS profiles,
  simulation_config.json, realtime setup status, and setup downloads."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# simulation-setup

Use this sub-skill when a task asks to prepare a MiroFish simulation after graph build: create a simulation record, inspect/filter graph entities, generate OASIS Agent profiles/personas, produce `simulation_config.json`, watch realtime Step 2 setup progress, download setup artifacts, or debug "no matching entities" and partial setup artifacts.

## Route first

- If the user still needs seed documents uploaded, ontology generated, graph build started/polled, or graph reset/delete, route to the sibling `graph-build` sub-skill.
- If the user asks to start/stop a simulation, monitor runtime rounds/actions/timelines/posts/comments/stats, interview agents, or finalize a live environment, route to the sibling `simulation-run` sub-skill after setup is ready.
- If the user asks for generated reports or report graph reads, route to the sibling `reporting` sub-skill after runtime completion.

## Read or run the bundled material

- Read [references/workflows.md](references/workflows.md) for the end-to-end Step 2 flow: create simulation, optional entity inspection, prepare, realtime profile/config polling, artifact validation, downloads, and handoff to `simulation-run`.
- Read [references/api-reference.md](references/api-reference.md) when constructing `/api/simulation` setup, entity, profile, config, download, environment-status, or close-env calls and interpreting response fields/statuses.
- Read [references/profile-formats.md](references/profile-formats.md) before validating `twitter_profiles.csv`, `reddit_profiles.json`, standalone `/generate-profiles` output, or `simulation_config.json` shape and platform defaults.
- Read [references/troubleshooting.md](references/troubleshooting.md) when setup fails, stalls, reuses stale artifacts, reports zero entities, receives an invalid platform, has partial JSON/CSV writes, or lacks required keys.
- Run [scripts/profile-format-smoke.py](scripts/profile-format-smoke.py) with `python scripts/profile-format-smoke.py --self-test` to smoke-check the bundled current profile-file formats without importing MiroFish or starting OASIS. Use `--help` for options.

## Minimal safe operating loop

1. Confirm there is a completed project graph: a `project_id`, a usable `graph_id`, and a non-empty project `simulation_requirement`.
2. Create or reuse a simulation record with `POST /api/simulation/create`; the UI default enables both Twitter and Reddit.
3. If entity readiness is uncertain, inspect `GET /api/simulation/entities/<graph_id>?enrich=false` first, then narrow with `entity_types` only after you see available custom labels.
4. Start preparation with `POST /api/simulation/prepare`. Do not pass runtime `max_rounds` here; setup generates time/config parameters from the simulation requirement.
5. Poll `POST /api/simulation/prepare/status` plus realtime `profiles/realtime` and `config/realtime` until `config_generated` is true and the simulation state is `ready` or the task fails with an explicit error.
6. Validate profile count, profile file format, `agent_configs`, `initial_posts[*].poster_agent_id`, enabled platform configs, and `state.json` flags before proceeding.
7. For `POST /api/simulation/start`, runtime status, interviews, close/stop, and graph-memory updates, switch to `simulation-run`.
