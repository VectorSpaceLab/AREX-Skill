# Repo provenance

- Schema: `disco.repo-provenance.v1`

## Source identity

- Public repo name: MiroFish
- Canonical generated skill id: `mirofish`
- Backend package name: `mirofish-backend`
- Backend package version: `0.1.0`
- Backend Python requirement: `>=3.11,<3.13`
- Frontend package version: `0.1.0`
- License in package metadata: `AGPL-3.0`

## Source revision baseline

- Git branch: `main`
- Git commit: `b5b53acc57189a4a42e44a23e149dc655c98fe82`
- Dirty state: dirty because generated `skills/` artifacts were untracked during construction.
- Working tree note: source evidence paths below were read from the baseline checkout and not from generated skill artifacts.

## Evidence paths used

Root and deployment evidence:

- `README.md`
- `README-ZH.md`
- `.env.example`
- `package.json`
- `Dockerfile`
- `docker-compose.yml`

Backend package evidence:

- `backend/pyproject.toml`
- `backend/requirements.txt`
- `backend/uv.lock`
- `backend/run.py`
- `backend/app/__init__.py`
- `backend/app/config.py`
- `backend/app/api/graph.py`
- `backend/app/api/simulation.py`
- `backend/app/api/report.py`
- `backend/app/services/graph_builder.py`
- `backend/app/services/ontology_generator.py`
- `backend/app/services/oasis_profile_generator.py`
- `backend/app/services/report_agent.py`
- `backend/app/services/simulation_config_generator.py`
- `backend/app/services/simulation_ipc.py`
- `backend/app/services/simulation_manager.py`
- `backend/app/services/simulation_runner.py`
- `backend/app/services/text_processor.py`
- `backend/app/services/zep_entity_reader.py`
- `backend/app/services/zep_graph_memory_updater.py`
- `backend/app/services/zep_tools.py`
- `backend/app/utils/file_parser.py`
- `backend/app/utils/llm_client.py`
- `backend/app/utils/locale.py`
- `backend/app/utils/logger.py`
- `backend/app/utils/ontology.py`
- `backend/app/utils/openai_chat_compat.py`
- `backend/app/utils/zep.py`
- `backend/app/utils/zep_lifecycle.py`
- `backend/app/utils/zep_paging.py`

Frontend evidence:

- `frontend/package.json`
- `frontend/vite.config.js`
- `frontend/src/App.vue`
- `frontend/src/api/graph.js`
- `frontend/src/api/simulation.js`
- `frontend/src/api/report.js`
- `frontend/src/views/Home.vue`
- `frontend/src/views/Process.vue`
- `frontend/src/views/SimulationView.vue`
- `frontend/src/views/SimulationRunView.vue`
- `frontend/src/views/ReportView.vue`
- `frontend/src/views/InteractionView.vue`
- `frontend/src/components/Step1GraphBuild.vue`
- `frontend/src/components/Step2EnvSetup.vue`
- `frontend/src/components/Step3Simulation.vue`
- `frontend/src/components/Step4Report.vue`
- `frontend/src/components/Step5Interaction.vue`

Verification-candidate evidence:

- `backend/tests/test_llm_json_responses.py`
- `backend/tests/test_ontology_generator.py`
- `backend/tests/test_openai_chat_compat.py`
- `backend/tests/test_platform_profiles.py`
- `backend/tests/test_report_tool_result_sanitizer.py`
- `backend/tests/test_simulation_prepare_failure.py`
- `backend/tests/test_zep_cloud_contracts.py`
- `backend/tests/test_zep_cloud_validation_script.py`
- `backend/tests/test_zep_entity_reader_edges.py`
- `backend/tests/test_zep_graph_lifecycle.py`
- `backend/tests/test_zep_retry_and_client.py`
- `backend/scripts/action_logger.py`
- `backend/scripts/test_profile_format.py`
- `backend/scripts/run_parallel_simulation.py`
- `backend/scripts/run_reddit_simulation.py`
- `backend/scripts/run_twitter_simulation.py`
- `backend/scripts/validate_zep_cloud_integration.py`

## Explicitly excluded or de-prioritized evidence

- Git metadata, caches, build artifacts, virtual environments, runtime uploads, and dependency directories.
- Root star-history maintenance scripts and tests, which are repository-maintenance tooling rather than MiroFish operating workflow guidance.
- CI/star-history files unrelated to using MiroFish.
- Live Zep Cloud validation as an automated verification source; it remains manual because it needs credentials and can create/delete Cloud graph resources.

## Refresh signals

Refresh this skill if any of these change:

- Backend API route names, payload fields, state names, or artifact layouts.
- Zep Cloud SDK version or lifecycle/delete/reset behavior.
- OASIS/CAMEL launcher parameters or profile/config formats.
- Frontend step order, API polling semantics, or default platform choices.
- LLM provider compatibility code, especially JSON-mode and GPT-5 request shaping.
- Docker/uv/npm setup commands or required environment variables.
