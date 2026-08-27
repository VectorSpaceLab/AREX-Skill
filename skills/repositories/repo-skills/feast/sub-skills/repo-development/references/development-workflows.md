# Feast Development Workflows

## Contributor Setup

Feast development is Python-first, with Go, Java, docs, UI, Helm, and operator components in the same repository. Start from the repository root and use the Makefile targets so commands match CI expectations.

Recommended setup commands:

```bash
make install-python-dependencies-dev
make install-python-dependencies-minimal
make install-precommit
```

What to expect:

- `make install-python-dependencies-dev` uses pinned Python requirement files for the current Python minor version and installs Feast editable.
- `make install-python-dependencies-minimal` installs the minimal editable package set for lighter validation.
- `make install-precommit` installs hooks for pre-commit, commit-msg, and pre-push stages.
- Python support is centered on Python 3.10, 3.11, and 3.12; the `pixi` manifest contains named environments such as `py310`, `py311`, and `py312` with `uv` available.

If setup is too heavy for the task, run scoped commands with the existing environment first and escalate only when imports or dependency checks fail.

## Source Tree Orientation

Common areas:

| Area | Purpose | Typical scoped checks |
|---|---|---|
| `sdk/python/feast/` | Python SDK, CLI, feature store orchestration, infra integrations | `uv run ruff check`, `uv run ruff format`, `uv run bash -c "cd sdk/python && mypy feast/<file>.py"` |
| `sdk/python/tests/unit/` | Fast local Python tests with no external service requirement | `uv run python -m pytest <test-file> -v` |
| `sdk/python/tests/integration/` | Service-backed, Docker-backed, or broad integration coverage | Run only with explicit prerequisites and authorization |
| `protos/` | Shared protobuf definitions for Python, Go, docs, and serving APIs | `make compile-protos-python` or `make protos` |
| `go/` | Go feature server and generated Go protobuf bindings | `make build-go`, `make test-go`, `make format-go`, `make lint-go` |
| `java/` | Java serving components and client | `make test-java`, `make build-java`, `make lint-java`, `make format-java` |
| `infra/feast-operator/` | Kubernetes operator and container build context | Use operator-local Makefile targets only when the change touches operator code |
| `docs/` | Main project documentation | Update navigation when adding pages |
| `infra/website/docs/blog/` | Blog posts only | Include frontmatter with `title`, `description`, `date`, and `authors` |

## Python Formatting, Linting, and Typing

Use the smallest relevant command before broad checks:

```bash
uv run ruff check sdk/python/feast/path/to/file.py
uv run ruff check --fix sdk/python/feast/path/to/file.py
uv run ruff format sdk/python/feast/path/to/file.py
uv run bash -c "cd sdk/python && mypy feast/path/to/file.py"
```

Broader targets:

```bash
make format-python
make lint-python
make mypy-full
make precommit-check
make precommit-all
```

Interpretation:

- `make format-python` runs Ruff autofix and formatting over `sdk/python/feast/` and `sdk/python/tests/`.
- `make lint-python` runs Ruff checks, Ruff format check, and MyPy for `sdk/python/feast`.
- `make mypy-full` type-checks both `feast` and `tests` under `sdk/python`.
- New Python files should use type hints; follow nearby module patterns and add `from __future__ import annotations` when consistent with the surrounding code.

## Test Command Escalation

Start targeted:

```bash
uv run python -m pytest sdk/python/tests/unit/test_unit_feature_store.py -k "test_apply" -v
uv run python -m pytest sdk/python/tests/unit/infra/registry/ -v
```

Then escalate:

```bash
make test-python-smoke
make test-python-unit-fast
make test-python-unit
make test-python-changed
```

Use broad integration only when safe:

```bash
make test-python-integration-local
make test-python-integration
make test-python-universal
```

Safety rule: do not run service-backed or cloud-backed tests unless required services, credentials, containers, and runtime budget are explicitly available. Prefer local/unit coverage for normal source edits.

## Go, Java, and Operator Awareness

Go feature server work commonly needs generated protobufs and local Feast install support:

```bash
make compile-protos-go
make build-go
make test-go
make format-go
make lint-go
```

Java serving work uses Maven through Makefile targets:

```bash
make test-java
make test-java-integration
make test-java-with-coverage
make build-java
make build-java-no-tests
make format-java
make lint-java
```

Operator and Docker targets can build images or use cluster tooling. Treat these as heavier checks; run only when the change touches those areas and the environment supports Docker/Kubernetes.

## PR Conventions

Before handoff or PR:

- Use semantic PR titles such as `feat:`, `fix:`, `ci:`, `chore:`, or `docs:`.
- Sign off commits with `git commit -s` when committing is requested.
- For public PRs, maintainers may need `ok-to-test` before Prow runs CI.
- Substantial architecture changes should go through RFC/ADR flow; finalized decisions become ADRs under the docs ADR area.
- Keep release/publish scripts as maintainer-reference context unless the user explicitly asks to work on release engineering.

## Safe Native Verification Selection

When selecting native checks for a future agent:

1. Map each changed path to the smallest nearby unit tests.
2. Add file-level Ruff and MyPy for changed Python implementation files.
3. Add protobuf generation if `.proto` files changed.
4. Add Go/Java checks only for changes under those trees or shared protobufs that affect them.
5. Record broad integration tests as skipped unless service prerequisites are present.

Example for a registry-related edit touching `sdk/python/feast/feature_store.py`:

```bash
uv run ruff check sdk/python/feast/feature_store.py sdk/python/tests/unit/test_unit_feature_store.py
uv run bash -c "cd sdk/python && mypy feast/feature_store.py"
uv run python -m pytest sdk/python/tests/unit/test_unit_feature_store.py -k "apply or registry or plan" -v
uv run python -m pytest sdk/python/tests/unit/infra/registry/ -v
make test-python-smoke
```
