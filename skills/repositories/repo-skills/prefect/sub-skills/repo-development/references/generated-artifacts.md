# Generated Artifacts and Source-of-Truth Files

Many Prefect files are generated from Python source, schemas, examples, or service definitions. Change the source of truth, then regenerate or validate the derived output; do not hand-edit generated outputs unless the scoped instructions explicitly say the file is hand-authored.

## Generation Command Map

| Artifact area | Source of truth | Typical command |
| --- | --- | --- |
| Settings schema/reference/types | `src/prefect/settings/`, settings models | `just generate-settings` |
| Settings type file | `src/prefect/settings/base.py`, `models/` | `just generate-settings` or the generated-settings pre-commit hook |
| `prefect.yaml` JSON schema | Deployment models/templates and schema generator | `just generate-prefect-yaml-schema` |
| OpenAPI/Mintlify REST docs | FastAPI server routes and schemas | `just generate-openapi` |
| Python API reference docs | Python modules under `src/prefect/` | `just api-ref <module>` or `just api-ref-all` |
| CLI command reference docs | Cyclopts CLI definitions | `just generate-cli-docs` |
| Example docs pages | Top-level `examples/` Python files | `just generate-examples` |
| All major docs artifacts | Multiple generators | `just generate-docs` |
| UI-v2 OpenAPI service types | Server API/schema changes consumed by UI-v2 | UI-v2 `service-sync` pre-push hook or `npm run service-sync` from `ui-v2/` |
| Integration API docs | Integration package source | `just api-ref` from inside the integration directory when available |
| `uv.lock` | `pyproject.toml` dependency metadata | `uv lock` or pre-commit `uv-lock` hook |

Use the repository's generation recipes or pre-commit generation hooks when the goal is to update several derived artifacts together. Run only the generators appropriate for the changed source-of-truth files.

## Docs Rules

- Current Prefect docs live under `docs/v3/`.
- Docs files use `.mdx` with lowercase YAML frontmatter. The `title` renders as H1, so body content starts at `##`.
- Register navigable pages in `docs/docs.json`; hidden pages do not require navigation registration.
- Use absolute docs-root links without `.mdx`, such as `/v3/concepts/flows`.
- Use Mintlify components instead of Markdown-native admonition syntax.
- Do not edit generated docs under `docs/v3/examples/`, `docs/v3/api-ref/python/`, `docs/v3/api-ref/cli/`, generated REST endpoint pages, or integration `api-ref/` directories. The hand-authored exception is `docs/v3/api-ref/events/`.
- When moving docs pages, add redirects in `docs/docs.json`.
- Prefer snippets from `docs/snippets/` before duplicating shared content.
- Cloud-only features need an explicit Cloud marker or note.

Useful docs commands:

```bash
just docs
just links
just lint
just generate-docs
```

The root `just docs` starts the Mintlify dev server; the docs-local `justfile` also provides `docs`, `links`, and `lint` recipes.

## Settings Changes

When adding or moving settings:

1. Put the setting in the correct settings group under `src/prefect/settings/models/`.
2. Use `Field()` with `build_settings_config(...)`; do not add `validation_alias` for new settings unless maintaining legacy compatibility.
3. Update `Settings` composition if a new group is introduced.
4. Update `SUPPORTED_SETTINGS` in `tests/test_settings.py` with a test value.
5. Regenerate settings types and schemas as needed.

Validation examples:

```bash
uv run pytest tests/test_settings.py -x --tb=short
just generate-settings
uv run pre-commit run generate-settings-types --all-files
```

## API and Schema Changes

Server API changes can affect several derived outputs:

- REST OpenAPI docs under generated docs directories.
- UI-v2 service types when server API, server schemas, server events, or server utility schemas change.
- Client and server schema compatibility when mirrored models exist.
- `prefect-client` package build if client-visible imports or dependencies change.

For API changes, consider:

```bash
uv run pytest tests/server/api/affected_area.py -x --tb=short
just generate-openapi
cd ui-v2 && npm run service-sync
```

Run UI service sync only when the UI-v2 API contract is touched; it may install npm dependencies and is broader than a normal Python check.

## CLI Docs Changes

CLI commands are generated from Cyclopts definitions. If you change command names, options, help text, JSON output, or command grouping, run command tests first and regenerate CLI docs:

```bash
uv run pytest tests/cli/test_command_group.py -x --tb=short
just generate-cli-docs
```

For command behavior, preserve JSON output purity: suppress human-readable diagnostics whenever JSON output is active.

## Example Page Changes

Top-level examples can be transformed into docs pages. When an example changes:

```bash
uv run -s examples/example_file.py
just generate-examples
```

Avoid network, credentials, or long-lived services in generated examples unless they are clearly marked and test-skipped in docs infrastructure.

## `prefect-client` Synchronization

The separate `prefect-client` package uses `client/pyproject.toml` and copies a subset of `src/prefect/`.

When root dependencies affect client-side code:

1. Mirror compatible dependency changes in `client/pyproject.toml`.
2. Keep server-only dependencies out of client-side import paths.
3. Ensure `src/prefect/client/`, client schemas, and cross-system protocols can import after the client package strips server and CLI code.
4. Reproduce package-build failures with `bash client/build_client.sh` when needed.

Most common failure modes are a new client-visible import reaching server-only code, a missing dependency mirror, or assuming the CLI/testing modules exist in `prefect-client`.

## Integration Package Artifacts

Integrations are separately versioned packages under `src/integrations/prefect-*`. Work from inside the integration directory for package-specific tests or docs:

```bash
uv run pytest tests/ -k test_name
just api-ref
```

Do not run release scripts such as `just prepare-integration-release <pkg>` as routine validation; they generate release notes and can touch docs in ways unrelated to the code change.

## Stale Artifact Symptoms

Suspect stale generated files when:

- `pre-commit` modifies files after a seemingly complete change.
- Settings tests fail because a new env var is missing from supported settings or generated type maps.
- Docs CI reports missing generated pages, broken links, or outdated API/CLI reference content.
- UI-v2 type checks fail after server schema/API changes.
- `prefect-client` CI fails despite core tests passing.
- `uv-lock` modifies `uv.lock` after dependency metadata changes.

Regenerate from the nearest source of truth instead of patching derived output by hand.
