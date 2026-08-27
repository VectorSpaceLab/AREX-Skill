# Codebase Map and Test Target Selection

This map is for contributors changing SimpleTuner internals. For user-facing training, data preparation, model/adapter usage, WebUI operation, or cloud job operation, route to the task-specific SimpleTuner sub-skill unless the user is editing that implementation.

## Entry Points and Package Surface

- `st_cli.py` and `simpletuner/cli/`: root CLI parser and subcommands.
- `simpletuner/train.py`: training console entry point.
- `simpletuner/configure.py`: configuration console entry point.
- `simpletuner/inference.py`: inference console entry point.
- Package metadata lives in `pyproject.toml`, `setup.py`, `MANIFEST.in`, and generated distribution metadata.
- Verified console entry points include `simpletuner`, `simpletuner-train`, `simpletuner-configure`, and `simpletuner-inference`.

## Core Source Areas

| Area | Source map | Common tests |
|---|---|---|
| Configuration/options | `simpletuner/helpers/configuration/`, `config/*.example`, `st_cli.py`, `simpletuner/cli/configure.py`, `documentation/OPTIONS*.md` | `tests.test_config`, `tests.test_config_registry`, `tests.test_config_templates`, `tests.test_loader_boolean_handling`, `tests.test_parser_type_override`, `tests.test_cli_environment` |
| Data backend/dataloader | `simpletuner/helpers/data_backend/`, `simpletuner/helpers/caching/`, `simpletuner/simpletuner_sdk/server/data/dataset_blueprints.py`, `simpletuner/templates/components/dataloader/`, `documentation/DATALOADER*.md`, `documentation/data_presets/` | `tests.test_backend_config`, `tests.test_audio_backend_config`, `tests.test_dataset_blueprints`, `tests.test_dataset`, `tests.test_dataset_plan`, `tests.helpers.data_backend.test_local_files`, `tests.helpers.data_backend.test_caption_pipeline` |
| Models/adapters/field registries | `simpletuner/helpers/models/`, `simpletuner/helpers/models/model_metadata.json`, `simpletuner/helpers/training/lora_format.py`, `simpletuner/helpers/models/field_registry/`, `simpletuner/simpletuner_sdk/server/services/field_registry/` | `tests.test_model_field_registry`, `tests.test_lora_format`, model-family tests named `tests.test_<family>_model`, LoRA target tests, pipeline tests, transformer tests |
| Training/distributed/checkpointing | `simpletuner/train.py`, `simpletuner/helpers/training/`, `simpletuner/helpers/acceleration/`, attention/FSDP/context-parallel docs | `tests.test_trainer`, `tests.test_training_service`, `tests.test_training_checkpointing`, `tests.test_attention_backend`, `tests.test_context_parallel_plans`, `tests.test_fsdp_cmd_args`, checkpoint/resume tests |
| WebUI/server/API | `simpletuner/simpletuner_sdk/server/app.py`, `webui_app.py`, `routes/`, `services/`, `templates/`, `static/js/`, `tests/pages/`, `tests/webui_test_base.py` | `tests.test_api_integration`, `tests.test_server_modes`, `tests.test_server_startup_integration`, `tests.test_dataset_routes`, `tests.test_template_rendering`, `tests.test_webui_e2e`, JS tests |
| Cloud/queue/workers | `simpletuner/cli/cloud/`, `simpletuner/cli/jobs.py`, `simpletuner/simpletuner_sdk/server/routes/cloud/`, `simpletuner/simpletuner_sdk/server/services/cloud/`, `simpletuner/worker_agent.py`, `simpletuner/service_worker.py` | `tests.test_cli_cloud_commands`, `tests.test_cloud_cli`, `tests.test_cloud_services`, `tests.test_cloud_state_paths`, `tests.test_local_job_queue_integration`, `tests.test_queue_routes`, auth/approval/quota tests |
| JavaScript | `simpletuner/static/js/`, `tests/js/`, templates wiring Alpine data/events | `npm test`, focused `tests/js/*.test.js`, plus Selenium E2E for wired browser behavior |
| Docs/i18n | `documentation/`, `mkdocs.yml`, section index pages | Docs build when dependencies are available; otherwise validate file coverage, suffix translations, nav/index updates, and affected tests. |
| Publishing/model cards | `simpletuner/helpers/publishing/`, publishing routes/services, model-card helpers | `tests.test_publishing_config_parsing`, `tests.test_publishing_providers`, `tests.test_publishing_service`, `tests.test_model_card`; privacy scan public payloads. |

## Test Selection Heuristics

1. Start from the changed source file's nearest matching tests.
2. Add regression tests that fail before the fix or assert the root cause.
3. Add integration/E2E tests when the bug depends on cross-module wiring.
4. Run broader suites when shared registries, templates, parsers, package metadata, or server startup are touched.
5. Do not mark CUDA-only unless the behavior truly requires third-party compiled CUDA kernels or comparable accelerator-only runtime.

Use `scripts/select_unittest_targets.py` to generate a first-pass command list. The helper is conservative; human review still decides whether model-specific, transformer, pipeline, Selenium, docs, or full-suite validation is required.

## Source Script Decisions

No release, deployment, cloud, or docs-generation source script is bundled by this sub-skill. Scripts such as deployment helpers or generated webhook documentation helpers are reference-only for maintainers because they can publish, deploy, rewrite docs, or assume external services. The bundled helpers here are new policy helpers derived from contributor instructions, test tree evidence, frontend test evidence, documentation rules, and privacy requirements.

## Representative Difficult Choices

### Dataloader option plan review

A valid plan for adding a dataloader option must identify the config class or validator, the runtime consumer, the WebUI Dataset template or dataset blueprint, `DATALOADER` documentation and translations, `OPTIONS` documentation if exposed globally, and focused tests. Missing the WebUI Dataset template or translations is a plan defect, not a small follow-up.

### Dirty-form WebUI bug

For a dirty-form bug, the minimum useful test set includes a focused JS test for local store behavior plus Selenium E2E for the real page. Use `FormDirtyStateFlowTestCase` and `EasyModeFormDirtyTestCase` because they cover direct load, Easy Mode, full form, tab switch, save-clears, and re-edit behavior. Jest alone cannot prove Alpine modifiers or event bubbling.
