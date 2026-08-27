# Source Map for Mycodo Development

This reference distills repository-relative source ownership for Mycodo development. Paths are relative to a Mycodo checkout and are not links to a private checkout.

## Version and provenance cues

Inspected facts: README latest version `8.17.0`; `mycodo/config.py` has `MYCODO_VERSION = '8.17.0'` and `ALEMBIC_VERSION = '5966b3569c89'`; top changelog release is `8.17.0 (2026.08.02)`; newest observed Alembic revision is `5966b3569c89_add_favicon_options.py`; CI targets Python 3.11. Refresh these together before release/provenance updates: README, config constants, changelog, Alembic head, workflow Python, requirements pins, and public claims about supported OS/install layout.

## Top-level map

| Area | Owner role | Development notes |
|---|---|---|
| `mycodo/` | main Python application package | Flask app, daemon/controllers, modules, tests, scripts, config, utilities. |
| `alembic_db/` | settings DB migrations | Alembic environment, revisions, and post-upgrade data transformations. |
| `docs/` | manual/API output | Mixed generated and hand-authored docs; identify owner before editing. |
| `docs_templates/` | translated docs source | Source templates for translated About, Data-Viewing, and index pages. |
| `install/` | installer/service/dependency inputs | requirements, systemd/nginx/logrotate/setup; inspect but do not execute casually. |
| `docker/` | container deployment | not verified by this production run. |
| `.github/workflows/` | CI recipe | heavy CI setup; use as evidence, not as a default local test plan. |

## Core config and app factory

- `mycodo/config.py` owns version constants, path constants, database/log paths, language list, Dashboard widget choices, themes, `ProdConfig`, and `TestConfig`.
- Public docs/changelog use `/opt/Mycodo` as installed-layout examples. For generic development guidance use `/path/to/Mycodo`.
- `TestConfig` uses in-memory SQLite, disables rate limiting, sets `TESTING = True`, and is the safe app-test configuration.
- `mycodo/mycodo_flask/app.py` owns `create_app()`, extension registration, blueprint registration, widget endpoint registration, Babel locale selection, Flask-Login API key loading, and unauthorized behavior.
- `mycodo/mycodo_flask/extensions.py` owns shared SQLAlchemy/Marshmallow extension objects.

## Flask web UI ownership

| Surface | Path pattern | Notes |
|---|---|---|
| route modules | `mycodo/mycodo_flask/routes_*.py` | Blueprints for admin/auth/dashboard/function/general/input/method/output/page/password reset/remote/settings/static. Keep route dispatch thin. |
| forms | `mycodo/mycodo_flask/forms/forms_*.py` | WTForms fields, choices, validators, SubmitFields. Choices often come from parser utilities and translations. |
| utilities | `mycodo/mycodo_flask/utils/utils_*.py` | persistence, custom option JSON, dependency checks, daemon/client calls, page-specific mutation logic. |
| templates | `mycodo/mycodo_flask/templates/` | Jinja pages/fragments, route marker comments, CSRF/AJAX, dependency prompts. |
| static | `mycodo/mycodo_flask/static/` | CSS/JS/assets and user static directories. Treat generated/vendor assets cautiously. |
| translations | `mycodo/mycodo_flask/translations/` | Babel `messages.pot` and `.po` catalogs; source strings come from Python/Jinja. |

Common page edit chain: model/metadata if data shape changes, WTForms class, utility mutator, route branch, template/static UI, then focused software tests.

## REST API ownership

- `mycodo/mycodo_flask/api/__init__.py` creates the `/api` Blueprint, Flask-RESTX `Api`, v1 vendor JSON representation (`application/vnd.mycodo.v1+json`), API-key auth metadata, default response text, and `init_api(app)` imports.
- API modules cover camera, choices, controller, daemon, dependency, export/import, function, input, logs, measurement, note, output, PID, and settings.
- API route classes inherit `flask_restx.Resource`. Fields live in the module or shared SQL schema helper.
- Test clients should include `Accept: application/vnd.mycodo.v1+json` and base64 `X-API-KEY` headers for authenticated API checks.
- Private construction evidence found 14 API modules. High-risk groups: measurement writes/readbacks require InfluxDB; daemon/dependency/export-import/camera routes can cross service/filesystem boundaries.

## Controllers and modules

Mycodo organizes runtime behavior around dynamically parsed module metadata.

| Type | Module directory | Base class/convention | Metadata dict | Parser |
|---|---|---|---|---|
| Inputs | `mycodo/inputs/` | `AbstractInput` | `INPUT_INFORMATION` | `parse_input_information()` |
| Outputs | `mycodo/outputs/` | `AbstractOutput` | `OUTPUT_INFORMATION` | `parse_output_information()` |
| Functions | `mycodo/functions/` | `AbstractFunction` | `FUNCTION_INFORMATION` | `parse_function_information()` |
| Actions | `mycodo/actions/` | `AbstractFunctionAction` | `ACTION_INFORMATION` | `parse_action_information()` |
| Widgets | `mycodo/widgets/` | widget module convention | `WIDGET_INFORMATION` | `parse_widget_information()` |

Custom directories exist for each family. Parsers include custom modules unless called with `exclude_custom=True`; generated Supported-* docs should exclude custom modules. Private catalog evidence counted approximately 141 Inputs, 46 Outputs, 36 Functions, 41 Actions, and 14 Widgets; refresh counts from the current checkout rather than hard-coding them.

Metadata fields that ripple outward:

- unique ids/names affect stored identifiers, Add dropdowns, duplicate detection, and generated docs;
- `measurements_dict`/`channels_dict` affect DeviceMeasurements rows, channel options, InfluxDB writes, graph choices, and API settings responses;
- `interfaces`, I2C/UART/FTDI/GPIO/Bluetooth fields, `options_enabled`, and custom options affect forms and docs;
- `dependencies_module` and `dependencies_message` drive dependency UI/docs and may describe apt, PyPI, or bash-command installs; do not execute them without approval;
- `execute_at_creation/modification/deletion` can run side effects; guard tests with `TESTING` and mocks.

## Database model map

Models live in `mycodo/databases/models/` and are imported through the model registry. `CRUDMixin.save()`/`delete()` commit through Flask-SQLAlchemy. Major tables include Input/InputChannel, Output/OutputChannel, CustomController/FunctionChannel, PID, Conditional, Trigger, Actions, Widget, Dashboard, Camera, User/Role, Misc, settings units/measurements/conversions, notes, remote hosts, SMTP, and Alembic version. JSON-like custom options are usually text fields with MySQL/MariaDB `LONGTEXT` variants.

## Tests, scripts, docs

- Software tests: `mycodo/tests/software_tests/`; conftest patches common hardware modules and uses `TestConfig`.
- Manual tests: `mycodo/tests/manual_tests/`; real Raspberry Pi temperature, GPIO edge, I2C sensors/LCD/multiplexer, UART K30, camera, and Bluetooth/MiFlora. Do not run by default.
- Testing dependencies: `install/requirements-testing.txt` (pytest, mock, testfixtures, factory_boy, webtest).
- Base runtime pins: `install/requirements.txt`; docs site pins: `docs/requirements.txt`.
- Source scripts include docs/manual generation, pybabel extraction/update, upgrade checks, InfluxDB helpers, backup/restore, installer/upgrade commands, and broad pytest wrappers. Prefer the bundled `run_selected_checks.py` helper for safe focused checks.

Generated docs ownership:

- Supported Inputs/Outputs/Functions/Actions/Widgets derive from module metadata and renderer helpers.
- API docs derive from Flask-RESTX schema plus Redoc tooling.
- translated About/Data-Viewing/index docs derive from `docs_templates` and doc translation dictionaries/catalogs.
- Babel catalogs derive from Python/Jinja source strings.

## Unverified surfaces

This sub-skill does not prove Raspberry Pi GPIO/I2C/UART/1-Wire/Bluetooth/camera behavior, InfluxDB service health, daemon/nginx/systemd, SSL setup, Docker, full installer/upgrade, backup creation, or restore.
