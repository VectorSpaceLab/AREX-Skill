# Repository Provenance

Schema: `disco.repo-provenance.v1`

This skill was generated from Great Expectations (GX Core) repository evidence.

## Source Snapshot

- Source repository: Great Expectations / GX Core
- Current commit: `eec491e4487df4fedf3500e29172a30568ce5317`
- Branch: `develop`
- Exact tag: none found
- Package distribution/import: `great_expectations`
- Package version observed during inspection: `0+untagged.1.geec491e`
- Remote URL: `https://github.com/great-expectations/great_expectations`
- Working tree state during generation: dirty because this generated `skills/` tree was added during the workflow

## Primary Evidence Paths

- `README.md`
- `requirements.txt`
- `setup.py`
- `setup.cfg`
- `pyproject.toml`
- `great_expectations/__init__.py`
- `great_expectations/data_context/`
- `great_expectations/datasource/fluent/`
- `great_expectations/expectations/`
- `great_expectations/core/`
- `great_expectations/checkpoint/`
- `great_expectations/render/`
- `great_expectations/validator/`
- `docs/docusaurus/docs/core/`
- `docs/docusaurus/docs/snippets/`
- `tests/core/`
- `tests/data_context/`
- `tests/datasource/fluent/`
- `tests/expectations/`
- `tests/checkpoint/`
- `tests/actions/`
- `tests/render/`
- `tests/validator/`
- `tests/integration/common_workflows/`
- `tests/integration/data_sources_and_expectations/`

## Scope Decisions

Included scope focused on practical GX Core coding-agent workflows:

- Context creation and project configuration
- Fluent datasource, data asset, and batch definition setup
- Expectation classes and expectation suites
- Validation definitions, validation results, result formats, and unexpected rows
- Checkpoints, actions, notifications, and Data Docs

Excluded or reference-level scope:

- Contributed expectation packages under `contrib/`
- Older versioned docs and GX Cloud UI-only docs
- CI, release, docs build, and maintainer infrastructure
- Backend-specific native tests requiring cloud credentials, warehouses, Spark clusters, Docker services, or destructive cleanup
- Generated caches and build artifacts

## Refresh Guidance

Refresh this skill if any of these change materially:

- `gx.get_context` mode semantics or `DataContextConfig` fields
- Fluent datasource factory names, asset methods, or batch definition APIs
- `ExpectationSuite`, expectation class constructors, row condition, or parameter APIs
- `ValidationDefinition.run`, result-format behavior, or unexpected-row APIs
- `Checkpoint`, validation action classes, Data Docs configuration, or notification behavior
- Package entry points or CLI support appear in a future Great Expectations release
