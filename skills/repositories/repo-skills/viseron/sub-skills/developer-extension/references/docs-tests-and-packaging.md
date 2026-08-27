# Docs, tests, and packaging

This reference covers schema-derived docs, focused backend tests, safe schema inspection, and the source-root import caveat that matters when agents change developer-facing backend code.

## Schema-derived documentation

Viseron component documentation is generated from component and domain `CONFIG_SCHEMA` definitions. The important maintenance contract is:

- Human-readable option text belongs in the schema marker `description=` argument.
- Description constants should live beside key/default constants so renames are synchronized.
- Component docs metadata tags are inferred from supported domain modules. Use only supported domain names as tags: `camera`, `face_recognition`, `image_classification`, `license_plate_recognition`, `motion_detector`, `nvr`, `object_detector`, and `system`.
- Generated config JSON should not be edited by hand. Update the Python schema, then regenerate or inspect the schema output.
- Domain-level schemas should be nested back into the component-level schema where the domain key appears.

The maintainer docs-generation command writes Docusaurus files. Treat that writer as reference-only unless the task explicitly asks to update docs. For a safe read-only view, use the bundled helper below.

## Read-only schema helper

Use [`../scripts/inspect_component_schema.py`](../scripts/inspect_component_schema.py) to inspect one component without writing docs files.

Examples from this sub-skill directory:

```shell
python scripts/inspect_component_schema.py yolo --include-domains
python scripts/inspect_component_schema.py logger --max-depth 1
```

The helper:

- Imports `viseron.components.<component>` and summarizes `CONFIG_SCHEMA`.
- Optionally imports supported domain modules for that component and summarizes their domain `CONFIG_SCHEMA` values.
- Reports setup hooks (`setup`, `setup_domains`, `unload`) and domain import errors.
- Prints JSON to stdout.
- Does not create directories, write `config.json`, write `_meta.tsx`, or write `index.mdx`.

If the helper fails to import a component because an optional hardware/service package is missing, preserve that as optional-dependency evidence. Do not install broad accelerator packages just to inspect an unrelated schema.

## Focused test strategy

Prefer small behavior-backed tests before broad suites. Good test targets for developer-extension changes include:

- Component lifecycle: component config validation, missing component import, non-boolean setup returns, `ComponentNotReady`, safe mode, component state/error transitions.
- Domain lifecycle: dependency waiting, required/optional dependency validation, `DomainNotReady`, setup failure, unload order, entity cleanup, duplicate registration, and domain module unload hooks.
- Reload: config diff classification, component/domain/identifier changes, default-component restart-required handling, validation-abort behavior, cancelled retry handling, setup-plan ordering, and dependents of newly pending optional dependencies.
- Helpers: schema validators, templating helpers, and event/state/entity helpers when a component change touches them.

Useful pytest patterns:

```shell
pytest tests/components/test__init__.py -q
pytest tests/domains/test__init__.py -q
pytest tests/test_reload.py -q
pytest tests/helpers/test_validators.py -q
pytest tests/helpers/test_template.py -q
```

For a new detector component, add or adapt tests that assert:

1. `CONFIG_SCHEMA` accepts a minimal valid detector config and rejects malformed thresholds, labels, camera ids, or device options.
2. `setup_domains()` registers one domain per configured camera id with `RequireDomain("camera", same_identifier)`.
3. Domain setup returns `True`, registers the domain instance, and handles transient readiness with `DomainNotReady` rather than masking permanent errors.
4. `unload()` stops threads/queues/listeners and removes `vis.data` entries or entity state owned by that component/domain.
5. Identifier-level reload of one camera unloads the detector/NVR chain for that identifier but leaves unrelated identifiers intact.

Avoid full container builds, live camera streams, real notification sends, real MQTT brokers, or accelerator inference as strict verification unless the user explicitly asks and the required services/hardware are available. Keep such behavior documented as optional/unverified when it is not exercised.

## Development environment notes

The repository's documented development path is a VS Code dev container. Manual environments are possible but dependency-heavy. For this sub-skill, do not require a full dev container unless the task actually needs frontend/docs/container tooling. For backend component/domain work, a focused Python test environment with core dependencies is usually enough.

Common local commands to consider, in increasing scope:

```shell
pytest <focused-test-file-or-node> -q
pre-commit run pylint --all-files
pre-commit run --all-files
```

Use broad `pytest tests/`, docs lint, frontend lint, Docker Compose test containers, or release image builds only when the change requires that surface.

## Source-root packaging/import caveat

Some Viseron subprocess-related modules import a top-level module named `manager`. The project includes `manager.py` at the repository/distribution top level, and subprocess workers import it as `from manager import ...` rather than through `viseron.manager`.

Implications for agents:

- When running from a source checkout, run Python from the source root or otherwise ensure the source root is on `sys.path` so top-level `manager.py` is importable.
- When inspecting an installed package, verify that the distribution includes top-level `manager.py`; otherwise imports involving storage or detector subprocess workers may fail with `ModuleNotFoundError: No module named 'manager'`.
- Do not blindly rewrite `from manager import ...` to a package-relative import. Those workers may be invoked as subprocess entry files where top-level import behavior is intentional.
- When writing new multiprocessing or subprocess helpers, consider how the worker will be executed: module import path, current working directory, environment variables, and whether the top-level helper will be visible.
- The bundled schema helper intentionally avoids writing docs and keeps imports narrow, but component import can still trigger optional dependency or `manager.py` failures if a component imports subprocess support at module import time.

## Documentation and release boundaries

This sub-skill may guide backend docs generation and focused tests. It does not own release notes, CI workflow changes, image publishing, or full container build maintenance. If a backend change requires those surfaces, document the requirement and route the implementation to a broader maintainer workflow.
