# Repository maintenance reference

This reference distills repository-maintainer evidence from the root contributor
rules, `framework/AGENTS.md`, framework and datasets dev scripts, contributor
Sphinx docs, package metadata, and representative tests. All paths below are
relative to a Flower repository checkout.

## Maintainer mindset

Use the repository PR review philosophy before recommending changes:

- **Necessity:** each added block should be required for the requested behavior.
  Flag speculative abstractions, premature generalization, and dead paths.
- **Simplicity:** prefer less code when readability and correctness are
  preserved; avoid clever one-liners that make maintenance harder.
- **Readability:** prefer explicit names, small functions, shallow nesting, and
  linear control flow.
- **Local consistency:** compare with nearby modules before changing structure,
  names, errors, typing, or tests.
- **PR sizing:** flag changes that combine unrelated refactoring, behavior
  changes, cleanup, docs, and generated artifacts; suggest splits when needed.

When producing a PR review, use the repository's requested sections: critical
issues, simplicity/readability suggestions, consistency concerns, whether the PR
should be split, and a brief verdict.

## Project and packaging shape

### Framework package

- `framework/py/flwr/` is the typed Python source root (`py.typed` is present).
- `framework/pyproject.toml` uses `uv_build` with `module-name = "flwr"` and
  `module-root = "py"`; source distributions/wheels exclude tests and generated
  test helpers.
- The current inspected package metadata reported `flwr` version `1.34.0`,
  installed editable from `framework/` with base runtime dependencies only.
- Python support is `>=3.11,<4.0`. Local agent-oriented framework commands in
  repository instructions target Python `3.11.14`; CI also checks newer Python
  versions.
- Unit tests live next to source as `*_test.py` under `framework/py/flwr/`.
  Many tests use `pytest` parametrization; some older ones use `unittest`.
- `framework/proto/flwr/proto/` contains protobuf sources; generated Python and
  typing outputs live under `framework/py/flwr/proto/`.
- SQLAlchemy Core table metadata lives under
  `framework/py/flwr/supercore/state/schema/`; Alembic revisions live under
  `framework/py/flwr/supercore/state/alembic/versions/`.
- `framework/docs/source/` contains Sphinx docs; `framework/docs/build/` is
  generated output and should not be committed.
- `framework/e2e/` contains standalone apps and shell scripts used by CI. Treat
  them as optional maintainer smokes, not default safe unit checks.

### Flower Datasets package

- `datasets/flwr_datasets/` is the typed Python source root for the
  `flwr-datasets` distribution.
- `datasets/pyproject.toml` uses `hatchling`, packages `flwr_datasets`, and
  excludes tests from built distributions.
- The current inspected package metadata reported `flwr-datasets` version
  `0.6.0`, installed editable from `datasets/` with base runtime dependencies
  only.
- Python support is `>=3.11`. Optional extras are `vision` and `audio`.
- Unit tests live under `datasets/flwr_datasets/**/*_test.py`.

## Environment selection

Do not confuse three environments:

1. **Runtime/package-use environment:** enough to import and use installed
   `flwr` or `flwr_datasets`. The inspected runtime environment only had base
   editable installs and was not a full contributor setup.
2. **Framework contributor environment:** needed for `dev/test.sh`, protobufs,
   docs, mypy, pylint, docsig, paracelsus schema docs, license checks, wheel
   checks, and CI-parity scripts.
3. **Datasets contributor environment:** separate `datasets/` uv project used
   for Flower Datasets formatting, docs, unit tests, and optional e2e projects.

For framework development, run commands from `framework/` unless a command is
explicitly shown from the repository root. Preferred local command form after a
controlled sync is:

```bash
cd framework
uv run --no-sync --python=3.11.14 <command>
```

Synchronize intentionally when dependencies changed or the environment is
missing:

```bash
cd framework
uv sync --locked --python=3.11.14 --all-extras --all-groups
```

For Flower Datasets development, use the `datasets/` project:

```bash
cd datasets
uv sync --all-extras
# or use --frozen/--locked-style discipline when matching CI lock behavior
```

The datasets contributor docs explicitly prefer uv project commands such as
`uv add`, `uv add --dev`, `uv add --optional <extra>`, and `uv lock`; avoid
ad-hoc `uv pip` dependency changes in that project.

## Framework command families

Run these from `framework/` unless noted.

| Task | Command family | Notes |
| --- | --- | --- |
| Fast package-only gate | `uv run --no-sync --python=3.11.14 ./dev/test.sh false` | Skips e2e/docs/copyright extras in the script while still running core Python/TOML/schema/license checks. |
| Full framework quality gate | `uv run --no-sync --python=3.11.14 ./dev/test.sh` | CI/pre-commit-oriented broad gate. Includes pytest, docs formatting checks, schema docs check, and license checks. |
| Narrow unit test | `uv run --no-sync --python=3.11.14 python -m pytest py/flwr/path/to_test.py` | Prefer first for targeted code changes. Use `-k "name"` for focused selection. |
| Type check | `uv run --no-sync --python=3.11.14 python -m mypy py` | Strict mypy is configured. |
| Ruff lint | `uv run --no-sync --python=3.11.14 python -m ruff check py/flwr --no-respect-gitignore` | Use targeted paths for narrow edits. |
| Pylint | `uv run --no-sync --python=3.11.14 python -m pylint --ignore=py/flwr/proto py/flwr` | Generated protobufs are ignored. |
| Format | `uv run --no-sync --python=3.11.14 ./dev/format.sh` | Broad formatter; for narrow edits prefer targeted isort/black/ruff. Keeps generated protobufs excluded from Python formatters. |
| Docs build | `uv run --no-sync --python=3.11.14 ./dev/build-docs.sh` | Builds default English docs through Sphinx. System `pandoc` is required. |
| Full/versioned docs | `uv run --no-sync --python=3.11.14 ./dev/build-docs.sh full [DOC_VERSION]` | Uses the docs single-version build helper. |
| Build package | `uv run --no-sync --python=3.11.14 ./dev/build.sh` | Produces artifacts under `framework/dist/`; do not commit them. |
| Wheel checks | `uv run --no-sync --python=3.11.14 ./dev/test-wheel.sh` | Requires a prior build. Runs twine, pyroma, and check-wheel-contents. |

`framework/dev/test.sh` sets `RAY_ENABLE_UV_RUN_RUNTIME_ENV=0` for pytest
because Ray's uv runtime-env hook can stall under `uv run`. Use the same
environment variable when debugging Ray/simulation tests directly.

## Flower Datasets command families

Run these from `datasets/` unless noted.

| Task | Command family | Notes |
| --- | --- | --- |
| Setup | `uv sync --all-extras` | Use a frozen/locked sync when reproducing CI lock behavior. |
| Full datasets gate | `uv run ./dev/test.sh` | Runs isort, black, init checks, copyright, ruff, mypy, pylint, taplo, and pytest. |
| Narrow datasets test | `uv run python -m pytest flwr_datasets/path/to_test.py` | Use for focused partitioner/preprocessor/CLI changes before the full gate. |
| Format | `uv run ./dev/format.sh` | Formats Python, TOML, and docs notebooks; strips selected notebook metadata while keeping outputs. |
| Build package | `uv run ./dev/build.sh` | Uses `uv build --clear`; do not commit `dist/`. |
| Build docs | `uv run ./dev/build-flwr-datasets-docs.sh` | Regenerates API docs, removes generated `source/ref-api/*.rst`, then rebuilds HTML. |
| Optional e2e | From `datasets/e2e/<framework>/`: `uv sync --frozen`, then `uv run python -m unittest discover -p "*_test.py"` | Repeat per framework-specific e2e project only when needed. |

## Public API exposure guardrails

Flower's Python public API is defined by recursively following `__all__` from
the root package. The framework contributor docs explain that symbols listed in
API reference docs are public because the docs are generated from this recursive
export traversal.

For a new public framework symbol:

1. Import it in the nearest public `__init__.py` using the repository style,
   usually `from .module import Name as Name`.
2. Add the symbol name to `__all__` and keep `__all__` sorted; the dev tool
   `python -m devtool.init_py_check py/flwr` checks missing `__init__.py` files
   and sorted `__all__` lists.
3. Make sure the symbol is reachable from the intended public import path. Do
   not require users to import implementation modules such as
   `flwr.server.strategy.fedavg` when `flwr.server.strategy.FedAvg` is intended.
4. Add or update API/reference docs when the public surface changes, and add a
   test for the public import path.
5. Treat removal or behavior changes as compatibility-sensitive; prefer
   deprecation handling/tests unless the task explicitly calls for a breaking
   change.

In the inspected framework source, the root `flwr.__all__` exported
`agentapp`, `app`, `clientapp`, and `serverapp`; `simulation` existed as a lazy
legacy export outside `__all__`. Verify the current file before deciding whether
legacy imports are part of the surface you are changing.

Flower Datasets follows the same recursive `__all__` pattern from
`flwr_datasets`. Its root exports `FederatedDataset`, `metrics`, `partitioner`,
`preprocessor`, `utils`, and `visualization`; partitioners and preprocessors are
then exported from their package `__init__.py` files.

The bundled `scripts/check_public_api.py` complements, but does not replace,
repo checks: it imports packages and recursively verifies that every `__all__`
entry is present and importable. Public leaf modules that intentionally expose
module-level helpers without their own `__all__` still need direct import-path
tests.

## Generated protobuf workflow

- Edit protobuf sources under `framework/proto/flwr/proto/`.
- Do not hand-edit generated files under `framework/py/flwr/proto/`.
- Regenerate outputs from `framework/`:

```bash
uv run --no-sync --python=3.11.14 ./dev/protoc.sh
```

- Use the proto parity check in a clean tree or CI-parity context:

```bash
uv run --no-sync --python=3.11.14 ./dev/check-protos.sh
```

`check-protos.sh` reruns generation and fails if `framework/py/flwr/proto/`
differs from `HEAD`; in a dirty local tree it can report expected generated
changes. Wire-format changes need serialization/deserialization tests, commonly
near `framework/py/flwr/common/serde_test.py` or a module-specific test.

## Alembic migration workflow

For ordinary SQLAlchemy metadata changes, use the generator first instead of
hand-writing a migration file.

Schema metadata sources:

- `framework/py/flwr/supercore/state/schema/`
- generated schema documentation: `framework/py/flwr/supercore/state/schema/README.md`
- Alembic revisions: `framework/py/flwr/supercore/state/alembic/versions/`

Generator command from `framework/`:

```bash
uv run --no-sync --python=3.11.14 python -m dev.generate_migration "Describe schema change"
```

The generator creates a temporary SQLite database, upgrades it to all heads,
then runs Alembic autogenerate against the selected branch head. The default
branch target is `flwr@head`; pass `--head <branch>@head` only when intentionally
targeting another branch.

After generation:

1. Confirm the new revision's `down_revision` and branch target.
2. Confirm generated operations match the SQLAlchemy metadata change.
3. Review data migration logic for renames/removals.
4. Review SQLite compatibility, especially `batch_alter_table` blocks.
5. Update schema documentation when table metadata changed; `framework/dev/format.sh`
   regenerates it via `paracelsus`.
6. Run migration validation when schema work is involved:

```bash
uv run --no-sync --python=3.11.14 ./dev/check-migrations.sh
```

Runtime SQL in `SqlMixin.query()` callers must stay portable. Avoid dialect-only
constructs such as `IIF`, `strftime`, `julianday`, `datetime()`, `NOW()`,
`EXTRACT(EPOCH ...)`, `to_timestamp()`, and `IFNULL`; prefer standard constructs
such as `CASE WHEN` and `COALESCE`, and compute timestamps in Python before
binding. Migrations may use dialect-specific SQL when necessary.

## Docs guardrails

- Framework docs live under `framework/docs/source/`; build with
  `framework/dev/build-docs.sh` or from `framework/docs` with
  `uv run --project .. make html`.
- System `pandoc` is required for framework docs builds.
- Add new `.rst` pages under `framework/docs/source/` and link them from the
  appropriate index/toctree.
- Do not commit `framework/docs/build/`.
- Flower Datasets docs live under `datasets/docs/source/`; use
  `datasets/dev/build-flwr-datasets-docs.sh` to regenerate API docs and build
  HTML.

## Test selection by change type

| Change type | First checks | Broader checks |
| --- | --- | --- |
| Public framework import/export | Public import test near changed package, `python -m devtool.init_py_check py/flwr`, `python ../skills/disco/flower/sub-skills/repository-maintenance/scripts/check_public_api.py flwr` | Framework fast or full gate. |
| App/message/strategy internals | Targeted `py/flwr/.../*_test.py` such as message, clientapp, serverapp, strategy tests | Framework fast/full gate. |
| CLI parser/help changes | Targeted tests under `framework/py/flwr/cli/`, `supernode/cli/`, or `supercore/cli/` | Framework full gate if docs/help changed. |
| Protobuf source changes | `./dev/protoc.sh`, targeted serde/module tests | `./dev/check-protos.sh`, framework gate. |
| State schema changes | `python -m dev.generate_migration ...`, targeted schema/alembic tests | `./dev/check-migrations.sh`, framework gate. |
| Framework docs only | `./dev/build-docs.sh`; narrow doc formatting if available | Full framework gate when touching generated API or docs configuration. |
| Datasets partitioner/preprocessor | Targeted tests under `datasets/flwr_datasets/partitioner/` or `preprocessor/` | `uv run ./dev/test.sh` from `datasets/`. |
| Datasets CLI or package docs | Targeted CLI/docs checks | Datasets full gate and docs build. |

## Native evidence map for maintainers

Representative unit-test evidence inspected for this sub-skill includes:

- Framework root/public import evidence: `framework/py/flwr/__init___test.py`.
- CLI help/version/parser evidence: `framework/py/flwr/cli/cli_test.py`.
- Message/app/strategy behavior candidates under `framework/py/flwr/app/`,
  `framework/py/flwr/clientapp/`, `framework/py/flwr/serverapp/`, and
  `framework/py/flwr/serverapp/strategy/`.
- Schema and migration behavior: `framework/py/flwr/supercore/state/schema/*_test.py`
  and `framework/py/flwr/supercore/state/alembic/utils_test.py`.
- Flower Datasets behavior: `datasets/flwr_datasets/federated_dataset_test.py`,
  partitioner tests, preprocessor tests, and `datasets/flwr_datasets/cli/create_test.py`.
- `framework/e2e/*` is useful for selected repo-owned checks but should be run
  only with isolation because scripts can mutate local app directories and start
  services.
