# Testing, CI Selection, Docs, and Translations

Use this reference to choose the smallest honest validation loop for Mycodo development changes.

## Software tests vs manual hardware tests

Software tests live under `mycodo/tests/software_tests/` and are intended for CPU/CI execution when base and testing dependencies are installed.

Key software-test facts:

- `conftest.py` creates a Flask app with `TestConfig`, uses in-memory SQLite, and patches common hardware imports (`RPi`, `picamera`, `AM2315`, `tentacle_pi`, `Adafruit_BMP`, `Adafruit_TMP`, `w1thermsensor`, `sht_sensor`, `smbus2`).
- `test_mycodo_flask/test_endpoints.py` uses WebTest, fixture-created admin/guest users, base64 API keys, and the v1 vendor JSON media type.
- `test_inputs/test_abstract_input_class.py` is a fast smoke for `AbstractInput` contract behavior.
- `test_inputs/test_inputs.py` instantiates selected Input modules with `testing=True`, mocks `get_measurement()`, and checks iteration/read/string/error behavior. It is broader and may need more optional imports.
- `test_mycodo_flask/test_utils_settings.py` verifies custom Function module update behavior with temp dirs and mocked subprocess/user-group side effects.
- `test_influxdb/test_influxdb.py` writes and reads InfluxDB measurements. Do **not** run it unless an isolated InfluxDB service is explicitly prepared.

Manual tests live under `mycodo/tests/manual_tests/` and target real hardware or host devices: Raspberry Pi temperature, camera still capture, GPIO edge detection, I2C ADC/sensors/LCD/multiplexer, UART K30, and MiFlora/Bluetooth. Do not run them without explicit user approval, matching hardware, and safe wiring.

## CI recipe distilled

The CI workflow is intentionally heavy: Ubuntu 24.04, Python 3.11, apt packages, WiringPi/Pigpio/InfluxDB setup, virtualenv creation, SSL cert generation, translations compilation, widget HTML generation, manual doc generation, a Flask frontend startup smoke, Node 20 plus global Redoc tooling, API doc generation, then all software tests.

For routine agent maintenance:

1. Run a focused helper check for the changed surface.
2. If a change spans app startup/API/database/module metadata, add one Flask/API-oriented software test selection.
3. Request full CI-like setup only for release validation or when the failure cannot be bounded.

## Bundled helper checks

Run the bundled helper from this sub-skill tree:

```bash
python path/to/development-and-testing/scripts/run_selected_checks.py --repo-root /path/to/Mycodo --list
python path/to/development-and-testing/scripts/run_selected_checks.py --repo-root /path/to/Mycodo import-smoke
python path/to/development-and-testing/scripts/run_selected_checks.py --repo-root /path/to/Mycodo upgrade-check pytest-abstract-input
python path/to/development-and-testing/scripts/run_selected_checks.py --repo-root /path/to/Mycodo pytest-custom-function-update --timeout 180
python path/to/development-and-testing/scripts/run_selected_checks.py --repo-root /path/to/Mycodo --dry-run pytest-flask-api-readonly
```

| Check | Validates | Does not prove |
|---|---|---|
| `import-smoke` | imports config, checks version constants, builds a TestConfig app, reports URL rules | hardware, daemon, production DB, InfluxDB, nginx/systemd |
| `upgrade-check` | runs lightweight Python minimum-version gate (default 3.11) | upgrade success, package installation, virtualenv repair |
| `pytest-abstract-input` | fast AbstractInput contract pytest | all Inputs or hardware behavior |
| `pytest-custom-function-update` | custom Function update software tests with mocked side effects | actual daemon restart or production custom directory mutation |
| `pytest-flask-api-readonly` | selected API/auth/readonly endpoint tests | every API route, InfluxDB write/read, dependency installer endpoints |

The helper prints commands, defaults to `import-smoke`, enforces timeouts, and never selects the full suite or manual hardware tests by default.

## Safe edit-test loops

### Pure import/config/version edits

1. Reconcile README latest version, `MYCODO_VERSION`, `ALEMBIC_VERSION`, changelog top entry, newest Alembic revision, and CI Python version.
2. Run `import-smoke`.
3. If Python support changed, run `upgrade-check` with the intended minimum version.

### Flask page/form/template/static edits

1. Identify route module, form class, utility mutator, template fragment, and static JS/CSS.
2. Preserve permissions, CSRF handling, flash/JSON message shape, and route marker comments used by tests.
3. Run `import-smoke`.
4. Run a focused endpoint/template pytest if covered; for auth/API-adjacent pages use `pytest-flask-api-readonly` or a narrower `pytest -k` selection.
5. Do not start production web UI, nginx, or systemd services without user approval.

### API endpoint changes

1. Read `database-and-api-development.md` for namespace/auth/media-type rules.
2. Preserve `Accept: application/vnd.mycodo.v1+json` and base64 `X-API-KEY` behavior unless intentionally changing API contract.
3. Add/update a focused software test using TestConfig and WebTest fixtures.
4. Run `import-smoke` and `pytest-flask-api-readonly` or the exact new endpoint test.
5. Mock or stop before side-effect endpoints such as dependency installation, daemon terminate, export/import, camera capture, or measurement writes against a real InfluxDB service.

### DB model and Alembic migration changes

1. Update the SQLAlchemy model and Marshmallow/API schema if exposed.
2. Add an Alembic revision with upgrade/downgrade and SQLite-safe batch operations for table alteration.
3. Add post-upgrade data migration only if existing rows need deterministic transformation.
4. Validate against a temporary database, not a real installed Mycodo database.
5. Run `import-smoke` plus the smallest Flask/API test that uses the affected field.

### Module metadata changes

1. Identify type: Inputs, Outputs, Functions, Actions, or Widgets.
2. Update the module metadata dict and parser handling only if needed.
3. Check ripples: Add dropdowns, dependency prompts, measurements/channels, custom options, generated Supported-* docs, and daemon controller startup.
4. Run `import-smoke` or a parse smoke in the prepared environment.
5. Regenerate only affected generated docs when tooling is available.
6. Do not install hardware dependencies just to import a module; use parser/mocking strategies or mark hardware coverage unverified.

### Custom Function update flow

Use `pytest-custom-function-update` when changing settings utilities that update custom Function modules. The test covers: no file/empty filename failures; same unique name with different upload filename; different unique name failure; invalid Python leaves existing file untouched; side-loaded modules update in-place; frontend reload and daemon restart calls are mocked and counted.

### InfluxDB-related code

InfluxDB is a service boundary. For query formatting or pure utility changes, prefer unit-level tests/mocks. Run InfluxDB tests only when an isolated InfluxDB service is intentionally prepared. Stop for approval if credentials, retention policy, service startup, database creation, or host ports are involved.

## Docs and generated output ownership

Generated module support pages derive from parser metadata:

- Supported Inputs: `parse_input_information(exclude_custom=True)`.
- Supported Outputs: `parse_output_information(exclude_custom=True)`.
- Supported Functions: `parse_function_information(exclude_custom=True)`.
- Supported Actions: `parse_action_information(exclude_custom=True)`.
- Supported Widgets: `parse_widget_information(exclude_custom=True)`.

Manual/API docs:

- manual page generation scripts write Markdown under `docs/` from metadata and templates;
- API docs are generated from the Flask-RESTX schema and Redoc tooling;
- full API manual generation may require Node/npm and Redoc; do not install global npm tools or run sudo without approval;
- `docs/requirements.txt` is for MkDocs/manual site building, not runtime app dependencies.

Translated docs and Babel catalogs:

- `docs_templates/` owns translated About, Data-Viewing, and index template source;
- docs translation generation fills template markers from doc translation dictionaries and Babel `.po` files;
- pybabel extraction updates `messages.pot` and language `.po` files from Python/Jinja source;
- compile-translations produces `.mo` files.

Safe translation loop: add/preserve `lazy_gettext` for import-time labels and `gettext` for request-time messages, run import/template smoke, extract/update catalogs only when Babel tooling exists, inspect `.pot`/`.po` diffs for accidental churn, and do not machine-translate unless requested.

## Dependency documentation

Dependency behavior is metadata-driven:

- base app pins: `install/requirements.txt`;
- testing pins: `install/requirements-testing.txt`;
- docs site pins: `docs/requirements.txt`;
- per-module prompts: `dependencies_module` and `dependencies_message` in Inputs, Outputs, Functions, Actions, Widgets.

Generated docs render dependency entries into apt/PyPI/link text. Dependency endpoints and scripts can mutate Python packages or system packages. Do not trigger them as routine validation.

## When to widen validation

Widen beyond helper checks only when the user asks for release/CI-level validation, a focused check fails due to integration uncertainty, shared app/model/parser behavior changed, generated docs/translations show unexpected broad diffs, or API/database compatibility must be proven across multiple endpoint groups. Keep hardware/service/system mutation boundaries explicit.
