# Maintenance Troubleshooting

Use this when repository maintenance checks fail or when a future agent needs to choose a safer validation path.

## Full Test Suite Avoidance

Symptom: a command such as `pytest`, `pytest tests`, or broad integration testing would take too long or require unavailable services.

Actions:

1. Stop and identify touched files plus behavior boundaries.
2. Prefer a specific `pytest tests/unit/...` target or a single integration test file only when the changed behavior requires it.
3. Use the bundled check selector to propose commands, then prune anything unrelated.
4. Report broad tests as skipped with the reason, not as silently omitted.

## Missing Dev Dependencies

Symptom: `ruff`, `mypy`, `pydoclint`, `yamlfix`, `pytest`, `alembic`, `lychee`, `zizmor`, or docs tooling is not found.

Actions:

1. Do not install broad extras without approval.
2. Recommend the minimal local setup for the requested validation, usually `pip install -e ".[server,dev]"` for full maintainer checks or a smaller extra for a specific area.
3. If only syntax safety is needed, run `python -m py_compile <files>` for changed Python files.
4. For missing `GH_TOKEN` in workflow linting, skip `zizmor` or instruct the user to provide `GH_TOKEN`; do not invent credentials.

## Docs GitBook URL and TOC Failures

Symptom: docs links pass local file checks but published URL expectations fail, or a new page does not appear in navigation.

Actions:

1. Inspect the relevant `toc.md`; public URL nesting follows TOC hierarchy, not only source path.
2. Use absolute `https://docs.zenml.io/...` links for OSS-to-Pro or Pro-to-OSS cross-section links.
3. Run relative-link checks for local Markdown and Lychee offline for local/image/HTML coverage.
4. Treat external link failures from bot-blocked domains separately from true `404`/`410` failures.

## US English Typos

Symptom: spelling checks fail on variants such as British spellings or custom technical terms.

Actions:

1. Prefer US English in docs, comments, docstrings, and UI strings.
2. Fix obvious spellings in source content.
3. Add project-specific terms only when they are intentional names and not a typo.
4. Avoid changing generated or vendored content unless the source is owned by ZenML.

## Unsafe Broad Integration Tests

Symptom: validation wants `tests/integration`, `zen-test environment provision`, Docker Compose, remote services, cloud credentials, or many optional integrations.

Actions:

1. Ask before provisioning services, building images, or using cloud credentials.
2. Prefer a single integration test file or import-boundary check.
3. For optional SDK changes, validate that base imports and `zenml --help` remain safe without installing that SDK.
4. Record skipped expensive checks and recommend CI or full/slow CI when local execution is impractical.

## Migration Branch or Upgrade Failures

Symptom: `alembic branches` reports diverging heads, `alembic upgrade head` fails, or a schema change lacks a migration.

Actions:

1. Run the branch check after adding migration files.
2. Do not edit old migrations already on shared branches; create a new migration instead.
3. Check domain models, SQLModel schemas, store methods, client methods, CLI filters, and docs for cross-layer consistency.
4. For realistic upgrade validation, populate data from the previous release or `develop`, switch to the current branch, then run `alembic upgrade head`.
5. Downgrades are usually optional; focus on upgrade correctness and backward-compatible rolling deployments.

## Optional Dependency and Import Boundary Failures

Symptom: base import, CLI help, tests, or type checks fail because optional server, SQL, or integration packages are imported too early.

Actions:

1. In integration flavor files, move optional SDK imports into `implementation_class` or use `TYPE_CHECKING` for type-only references.
2. In CLI and client-facing code, avoid top-level integration SDK imports.
3. Outside server internals, do not import from server modules; use shared models or `Client`.
4. Outside store internals, do not import SQL schemas directly; use `Client` or `client.zen_store` with proper dependency checks.
5. If a dependency bound changed, verify supported Python versions and whether dropping old versions is a breaking change.

## Formatting, Lint, and Mypy Failures

Symptom: `scripts/format.sh`, `scripts/lint.sh`, `ruff`, `pydoclint`, or `mypy` fails.

Actions:

1. Use `bash scripts/format.sh <changed paths>` for format/import cleanup when mutation is acceptable.
2. Run `ruff check <paths>` and `ruff format <paths> --check` on narrowed paths to isolate issues.
3. For docstring failures, update Google-style docstrings to match signatures and return types.
4. For mypy failures outside touched areas, avoid broad rewrites; report unrelated failures separately.

## PR and Release Label Problems

Symptom: CI fails release-label enforcement or PR readiness is unclear.

Actions:

1. Ensure exactly one label is expected: `release-notes` for user-facing changes or important bug fixes, `no-release-notes` for internal, CI, docs-only, refactor, or minor maintenance work.
2. Mention that PRs target `develop`.
3. Include checks run, skipped checks with reasons, user-facing docs impact, and whether slow/full CI is recommended.
4. Keep the summary focused on why the change is needed, not just what files changed.

## Command Selector Issues

Symptom: the bundled selector prints too many or too few commands.

Actions:

1. Treat selector output as a starting point, not an authority.
2. Add or remove commands based on the actual code path and nearest AGENTS guidance.
3. Never run suggested commands automatically from the selector; it is intentionally recommendation-only.
