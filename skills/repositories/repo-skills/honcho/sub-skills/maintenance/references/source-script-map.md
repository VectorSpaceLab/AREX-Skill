# Source Script Map for Maintenance

This map explains which Honcho source scripts to use directly, which behavior is mirrored by bundled skill helpers, and which scripts to exclude from maintenance-skill bundling.

## Use Source Script Directly

### `scripts/ensure_alembic_tests.py`

- Purpose: verifies every migration revision file has a matching `tests/alembic/revisions/test_<migration_basename>.py` file.
- Why use source directly: it is wired into pre-commit and should remain authoritative in the target checkout.
- Skill support: `scripts/maintenance_audit.py` includes a non-mutating migration/test correspondence check, useful as a quick audit or if reviewing a checkout where the source helper was modified.

### `scripts/run_alembic_tests.py`

- Purpose: maps changed migration/test files to the selective Alembic pytest pipeline. Infrastructure changes under `tests/alembic` run the full pipeline; specific revision/test changes use a `-k` revision-id expression.
- Why use source directly: it is wired into pre-commit and executes the repo's current pipeline command.
- Skill support: `scripts/alembic_test_selector.py` mirrors the command-selection logic and can print or run the selected command while reviewing patches.

### `scripts/update_version.py`

- Purpose: coordinates version and changelog updates for main API, Python SDK, TypeScript SDK, docs changelog, docs JSON, compatibility guide, README badge, and package metadata.
- Use headless flags for agent-safe operation. With no version flags it opens an editor.
- Do not bundle a replacement mutator: the script encodes current release-file paths and should stay authoritative in the checkout. The maintenance skill documents safe usage and post-run checks instead.

## Reference or Use Case by Case

### `.pre-commit-config.yaml`

- Treat as the authoritative hook inventory.
- Key local hooks: basedpyright, main pytest, selective Alembic pytest, Alembic coverage, Python SDK pytest, TypeScript build/typecheck.
- Preserve the note that TypeScript integration tests are not direct Bun tests; pre-commit runs build/typecheck, while pytest owns integration execution.

### `tests/bench/harness.py` and benchmark runners

- Use only for benchmark/performance or long-memory evaluation tasks.
- Exclude from routine maintenance verification because they start services, may need Docker/datasets/provider keys, and can be long-running.

### Utility scripts such as JWT, embeddings, provisioning, and DB migration helpers

- `scripts/generate_jwt.py`, `scripts/generate_jwt_secret.py`, `scripts/configure_embeddings.py`, `scripts/generate_message_embeddings.py`, `scripts/provision_db.py`, `scripts/migrate_db.py`, and `scripts/dialectic_cost_calculator.py` are operational utilities.
- Reference them only when the user's task targets auth tokens, embedding migration, DB provisioning, production migration, or cost analysis.
- Exclude from the maintenance sub-skill runtime because they can require credentials, live services, or target-specific deployment context.

## Bundled Skill Scripts

### `scripts/maintenance_audit.py`

- Non-mutating audit for a target Honcho checkout.
- Checks key files, migration-test correspondence, pytest/pre-commit/SDK guardrails, auth-policy test structure, LLM model-config regression anchors, and version-script headless flags.
- Use before or after broad maintenance work to catch obvious missing guardrails.

### `scripts/alembic_test_selector.py`

- Adapted command selector for changed Alembic-related files.
- Prints the pipeline command and optionally runs it with `--run`.
- Use to preview what the source `scripts/run_alembic_tests.py` should execute or to make a review note without invoking pre-commit.

## Exclusion Principles

Exclude a source script from bundling when it:

- Mutates release, database, deployment, docs, or package-registry state and the source repo script should remain authoritative.
- Requires credentials, provider APIs, Docker services, or datasets not guaranteed in ordinary maintenance.
- Is only relevant to a narrower operational sub-skill, such as auth token generation or embedding migration.
- Is too coupled to current repo release-file layout to be safer than using the source script directly.
