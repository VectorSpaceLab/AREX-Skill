# Testing Guide

## Framework Policy

SimpleTuner's Python test framework is `unittest`, not pytest. Use repo-relative commands and the repository-local virtual environment:

- Full preferred local suite: `.venv/bin/python -m unittest -v -f`
- Focused module: `.venv/bin/python -m unittest -v -f tests.test_config_registry`
- Multiple focused modules: `.venv/bin/python -m unittest -v -f tests.test_config tests.test_config_registry tests.test_loader_boolean_handling`
- Nested module: `.venv/bin/python -m unittest -v -f tests.helpers.data_backend.test_local_files`
- Discover-style CI equivalent: `python -m unittest discover -v tests/`

The full local suite averages about 300 seconds. Focused tests are appropriate during diagnosis and iteration, but do not use runtime cost as a reason to skip the full or integration validation required by the touched code path.

JavaScript tests use Jest through the npm scripts, not pytest:

- Full JS suite: `npm test`
- Focused JS file: `npm test -- tests/js/trainer_ui.test.js`
- Explicit Jest config: `npx jest --config tests/js/jest.config.js tests/js/trainer_ui.test.js`

Selenium E2E tests are `unittest` tests and are disabled unless explicitly enabled:

- Full WebUI E2E: `SIMPLETUNER_SELENIUM_TESTS=1 .venv/bin/python -m unittest -v -f tests.test_webui_e2e`
- Dirty-form focus: `SIMPLETUNER_SELENIUM_TESTS=1 .venv/bin/python -m unittest -v -f tests.test_webui_e2e.FormDirtyStateFlowTestCase tests.test_webui_e2e.EasyModeFormDirtyTestCase`
- Optional browser selection: prefix with `SELENIUM_BROWSERS=chrome` or another configured browser value.

## Focused vs Full Selection

Use a focused command first when the root cause is local and the relevant tests are known. Expand to the full suite or broader category when the change crosses configuration loading, training runtime, server startup, template rendering, shared field registries, package metadata, or public docs.

Before accepting a plan or implementation, check that the selected tests prove the stated root cause. If the plan cannot name affected functions/files and expected failures, stop and request a better plan.

## Area-to-Test Matrix

| Touched area | Representative files | Suggested focused tests |
|---|---|---|
| CLI/config parser/options | `st_cli.py`, `simpletuner/cli/`, `simpletuner/helpers/configuration/`, `config/*.example`, `documentation/OPTIONS*.md` | `.venv/bin/python -m unittest -v -f tests.test_config tests.test_config_registry tests.test_config_templates tests.test_cli_environment tests.test_parser_type_override tests.test_loader_boolean_handling` |
| Dataloader/data backend | `simpletuner/helpers/data_backend/`, `simpletuner/helpers/caching/`, `simpletuner/simpletuner_sdk/server/data/dataset_blueprints.py`, `simpletuner/templates/components/dataloader/`, `documentation/DATALOADER*.md`, `documentation/data_presets/` | `.venv/bin/python -m unittest -v -f tests.test_backend_config tests.test_audio_backend_config tests.test_dataset_blueprints tests.test_dataset tests.test_dataset_plan tests.helpers.data_backend.test_local_files` |
| Model registry/model family | `simpletuner/helpers/models/`, `simpletuner/helpers/models/model_metadata.json`, model-owned field registries | Start with model-specific tests such as `.venv/bin/python -m unittest -v -f tests.test_model_field_registry tests.test_lora_format`; add matching `tests.test_<family>_model`, `tests.test_<family>_lora_targets`, `tests.test_pipelines.test_<family>_pipeline`, or `tests.test_transformers.test_<family>_transformer` when behavior changes. |
| Training/distributed/checkpointing | `simpletuner/train.py`, `simpletuner/helpers/training/`, `simpletuner/helpers/acceleration/`, attention/distributed docs | `.venv/bin/python -m unittest -v -f tests.test_trainer tests.test_training_service tests.test_training_checkpointing tests.test_attention_backend tests.test_context_parallel_plans tests.test_fsdp_cmd_args` |
| WebUI/API/server | `simpletuner/simpletuner_sdk/server/routes/`, `simpletuner/simpletuner_sdk/server/services/`, `simpletuner/templates/`, `tests/pages/`, `tests/webui_test_base.py` | `.venv/bin/python -m unittest -v -f tests.test_api_integration tests.test_server_modes tests.test_server_startup_integration tests.test_dataset_routes tests.test_template_rendering`; add Selenium E2E for real browser behavior. |
| Cloud/job queue/workers | `simpletuner/cli/cloud/`, `simpletuner/cli/jobs.py`, `simpletuner/simpletuner_sdk/server/routes/cloud/`, `simpletuner/simpletuner_sdk/server/services/cloud/`, worker modules | `.venv/bin/python -m unittest -v -f tests.test_cli_cloud_commands tests.test_cloud_cli tests.test_cloud_services tests.test_cloud_state_paths tests.test_local_job_queue_integration tests.test_queue_routes` |
| JavaScript UI logic | `simpletuner/static/js/`, `tests/js/`, templates that wire Alpine data or event handlers | `npm test` or `npm test -- tests/js/<focused>.test.js`; add Selenium E2E for event propagation, `formDirty`, Alpine reactivity, and direct-load wiring. |
| Publishing/privacy | `simpletuner/helpers/publishing/`, publishing routes/services, model-card text | `.venv/bin/python -m unittest -v -f tests.test_publishing_config_parsing tests.test_publishing_providers tests.test_publishing_service tests.test_model_card`; scan public text before publishing. |
| Package/setup/CI | `pyproject.toml`, `setup.py`, `MANIFEST.in`, `.github/workflows/python-tests.yaml`, npm metadata | `.venv/bin/python -m unittest -v -f tests.test_setup tests.test_setup_platform_dependencies`; run `npm test` if JS dependencies or scripts change. |

The bundled `scripts/select_unittest_targets.py` implements this matrix as a safe read-only helper.

## Dataloader Option Change Checklist

When a plan adds, renames, removes, or changes a dataloader/dataset configuration option, require all of the following before accepting it:

1. Root cause and exact option semantics.
2. Code change in the relevant config class, loader, validator, builder, runtime consumer, or route.
3. WebUI Dataset template or blueprint update, including the form section where the option appears.
4. `documentation/DATALOADER.md` update and all existing `DATALOADER.<locale>.md` translations.
5. `documentation/OPTIONS.md` and all `OPTIONS.<locale>.md` translations if the option is also exposed as a general trainer option.
6. Focused unit tests for parser/config/validation/template behavior.
7. Selenium E2E if the field affects Alpine state, event handling, dirty state, dynamic visibility, or direct-load wiring.

If a dataloader plan omits the WebUI Dataset template and translations, reject the plan as incomplete.

## Validation Notes

Validation summaries should name commands in repo-relative form only. Do not paste raw terminal output into public text when it can contain local identity. Summarize failures by test module, assertion, and root cause instead of copying machine-specific paths.
