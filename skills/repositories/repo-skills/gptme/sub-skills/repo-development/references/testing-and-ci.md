# Testing and CI

This reference is for **checkout maintenance**, not for running the entire repository test matrix every time. Use the smallest command set that plausibly covers the change.

## What CI usually runs

The repo's workflows show the core maintenance gates:

- `make lint`
- `make typecheck-coverage` in the typecheck job
- `make check-openapi`
- `make test`
- `make test SLOW=1` in broader test coverage jobs
- Web UI checks from `webui/`:
  - `npm run typecheck`
  - `npm run lint`
  - `npm test`
  - `npm run build`
  - packaging verification through `make bundle-webui` and `make validate-release-package`

## Pytest markers to remember

The test suite uses these markers in `pyproject.toml`:

- `slow` — slower tests; excluded by the default fast run
- `eval` — eval-oriented tests; generally not part of fast maintenance loops
- `requires_api` — needs live API access or credentials
- `integration` — external-service integration tests
- `x11` — needs a real or headless X11 display
- `serial`, `timeout`, `flaky`, `no_retry`, `xdist_group` — execution controls, not selection hints

Practical rule:

- use `-m 'not slow and not requires_api'` for normal focused Python checks;
- add `requires_api` only when you deliberately have the needed credentials and network access;
- keep `x11` / browser / desktop tests out of the default local loop unless the change is specifically about them.

## Focused test selection patterns

These are representative, not exhaustive. The bundled helper [suggest_focused_tests.py](../scripts/suggest_focused_tests.py) applies similar routing automatically when run from this sub-skill directory or via its linked path.

### Server/backend code

Use these for changes under `gptme/server/`:

```bash
pytest tests/test_server*.py -q -m 'not slow and not requires_api'
```

Tighter examples for common server files:

- `gptme/server/api_v2_sessions.py` → `pytest tests/test_server_v2_sessions.py tests/test_server_v2_sse.py -q -m 'not slow and not requires_api'`
- `gptme/server/auth.py` → `pytest tests/test_server_auth.py tests/test_server_host_validation.py tests/test_server_cors.py -q -m 'not slow and not requires_api'`
- `gptme/server/client.py` → `pytest tests/test_server_client.py -q -m 'not slow and not requires_api'`
- `gptme/server/openapi_docs.py` → `make check-openapi`

### CLI / conversation / agent code

Use these for changes under `gptme/cli/`, `gptme/chat.py`, `gptme/logmanager/`, `gptme/agent/`, `gptme/message.py`, or related command plumbing:

```bash
pytest tests/test_cli.py tests/test_commands*.py tests/test_chats*.py tests/test_agent*.py -q -m 'not slow and not requires_api'
```

Add `tests/test_logmanager.py`, `tests/test_message.py`, or `tests/test_util*.py` when the diff touches persistence or formatting utilities.

### Tools / hooks / plugins / lessons / MCP

For maintainer changes in those areas, keep to the narrowest feature slice you can name:

```bash
pytest tests/test_tools*.py tests/test_plugins.py tests/test_hooks*.py tests/test_lessons*.py tests/test_mcp*.py -q -m 'not slow and not requires_api'
```

### Web UI and backend↔frontend coupling

When the diff touches `webui/src/**`, `webui/e2e/**`, or server code that affects frontend data flow, combine backend and frontend checks:

```bash
pytest tests/test_server*.py -q -m 'not slow and not requires_api'
cd webui && npm test
cd webui && npm run typecheck
```

For Playwright specs specifically:

```bash
cd webui && npm run test:e2e -- e2e/<file>.spec.ts
```

For TypeScript/React source changes, `npm run lint` is usually the next step after the focused unit test.

### Docs / packaging / metadata

- `.rst` docs changes → run the bundled `check_rst_patterns.py` against the target checkout's `docs/` directory first, then `make docs` when you need the full build.
- `pyproject.toml`, `poetry.lock`, or release metadata changes → run the bundled `check_python_project_health.py --root "$TARGET_GPTME_CHECKOUT"`.
- release artifact or bundling changes → run the bundled `check_release_package_contents.py` against built `dist/*.whl` and `dist/*.tar.gz` files after building packages.

## How to shrink a test set

When the default feature group is still too broad:

1. Prefer the exact changed test file if one exists.
2. Use `-k` for a single class/function inside a known test file.
3. Keep `-m 'not slow and not requires_api'` unless the change specifically needs API-backed or slow coverage.
4. If the change spans backend + Web UI, do not skip the frontend command just because the backend tests pass.

## What not to do here

- Do not treat `make test`, `make lint`, or `npm test` as background tasks.
- Do not run the entire suite just to confirm a small edit.
- Do not mix eval-suite validation into this workflow; that belongs in the eval-focused sub-skill.
