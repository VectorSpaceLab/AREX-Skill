# Quick commands for Observal work

Use these commands from a source checkout unless the user is only operating the installed CLI.

## Install and smoke

```bash
uv tool install --editable .
observal --version
observal --help
observal scan --help
observal doctor --help
```

The published CLI can be installed with `uv tool install observal-cli` or `pipx install observal-cli`.

## Default checks

| Goal | Command | Notes |
| --- | --- | --- |
| Python tests | `make test` | Runs root `tests/` from the server package context with pytest-xdist; mocks externals. |
| Verbose Python tests | `make test-v` | Same suite with verbose output. |
| Python lint | `make lint` | Ruff check over the repo. |
| Autoformat/fix | `make format` | Ruff format and fix. Inspect diffs after running. |
| Pre-commit all files | `make check` | Broad policy gate; may be slower than focused checks. |
| Fuzz smoke | `make test-fuzz` | Uses Atheris/Hypothesis seed corpus smoke. |
| Sync bundled CLI command reference | `make sync-skill` | Required after CLI command inventory or flags change. |

## Focused Python tests

When touching a specific area, prefer focused tests before broad Make targets:

```bash
cd observal-server
uv run --with pytest --with pytest-asyncio --with pyyaml --with typer --with rich pytest ../tests/test_cmd_scan.py -q
uv run --with pytest --with pytest-asyncio --with pyyaml --with typer --with rich pytest ../tests/test_harness_registry.py -q
uv run --with pytest --with pytest-asyncio --with pyyaml --with typer --with rich pytest ../tests/test_health.py -q
```

Package-local test directories are not included by the default `make test` target. Run them directly when relevant:

```bash
cd observal-server
uv run --with pytest --with pytest-asyncio --with pyyaml --with typer --with rich pytest ../observal_cli/tests/ -q
uv run --with pytest --with pytest-asyncio --with pyyaml --with typer --with rich pytest tests/ -q
```

## Web checks

Use the web package manager through the root workspace or from `web/`:

```bash
corepack pnpm --filter web typecheck
corepack pnpm --filter web lint
corepack pnpm --filter web build
corepack pnpm --filter web exec playwright test --list
```

Run actual Playwright specs only when a running stack and browser dependencies are available:

```bash
cd tests/e2e && corepack pnpm test
```

## Docker stack

The Docker stack is for local development, live integration, and E2E—not ordinary unit tests.

```bash
make up
make logs
make rebuild-fast
make down
```

`make reset` is destructive because it removes volumes. Do not run it without explicit approval.

## Bundled skill helper checks

```bash
python scripts/check_observal_skill_tree.py --skill-root skills/disco/observal --pretty
python sub-skills/cli/scripts/check_cli_contract.py --repo-root . --pretty
python sub-skills/server/scripts/check_server_routes.py --server-path . --pretty
python sub-skills/harness-telemetry/scripts/check_harness_registry.py --repo-root . --pretty
python sub-skills/web/scripts/check_web_contract.py --repo-root .
python sub-skills/repo-development/scripts/inspect_observal_repo.py --repo-root . --pretty
```

Use these helpers as contract smoke checks for this skill. They do not replace focused native tests for actual code changes.
