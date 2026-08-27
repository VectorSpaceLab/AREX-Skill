# Feature Repository Configuration

## Repository Layout

A Feast feature repository is a directory that contains declarative feature-store state:

```text
feature_repo/
├── feature_store.yaml
├── .feastignore
├── data/
│   ├── registry.db
│   └── online_store.db
└── feature_definitions.py
```

Required and common files:

- `feature_store.yaml` must be at the repository root unless the CLI or SDK is given a custom config path.
- Python files in the repo define Feast objects. `feast plan` and `feast apply` recursively import Python files that are not ignored.
- `.feastignore` excludes Python files or directories from repo parsing. Add imperative scripts, notebooks helpers, virtualenvs, and generated files that should not be imported during `apply`.
- Local data and metadata commonly live under `data/`, but paths are project choices.

## Minimal Local Config

```yaml
project: my_project
registry: data/registry.db
provider: local
online_store:
  type: sqlite
  path: data/online_store.db
entity_key_serialization_version: 3
```

Key fields:

- `project` namespaces the feature store. It also must match a `Project(name=...)` object if the repo defines one.
- `provider` determines default execution behavior. `local` supports local development with file-based offline data and SQLite online storage.
- `registry` stores metadata. A plain string such as `data/registry.db` is a local file registry path relative to the repo.
- `online_store` configures online serving storage. For local workflows, use `type: sqlite` and a local `path`.
- `offline_store` is optional for simple local file workflows; explicit store blocks are used for other backends.

## Registry Forms

Simple file registry:

```yaml
registry: data/registry.db
```

Structured registry config:

```yaml
registry:
  registry_type: file
  path: data/registry.db
  cache_ttl_seconds: 600
```

SQL registry pattern:

```yaml
registry:
  registry_type: sql
  path: postgresql+psycopg://USER:PASSWORD@HOST:5432/DB
```

Notes:

- File registry paths are best kept inside the feature repo for local demos and tests.
- SQL registry paths require the relevant Python dependencies and reachable credentials.
- Registry server, MCP, TLS, and remote registry workflows belong in `../../servers-and-remote/SKILL.md`.

## Project Naming Rules

Use project names that are stable and safe across CLI, registry, and backend resources:

- Allowed: letters, numbers, underscores, and hyphens.
- Not allowed: names starting with `_` or `-`.
- Avoid changing `project` after a repo has been applied unless you intend to create or switch namespaces.
- If a repo defines exactly one `Project(name=...)`, it must match `project` in `feature_store.yaml`; otherwise Feast exits with `Project object name should match with the project name defined in feature_store.yaml`.
- If no `Project` object exists, Feast uses the `project` value from `feature_store.yaml`.
- Multiple `Project` objects in one repo are not supported by the apply path.

## Config Discovery from Python

The verified `FeatureStore` constructor shape is:

```python
FeatureStore(repo_path: str | None = None, config=None, fs_yaml_file=None)
```

Common usages:

```python
from pathlib import Path
from feast import FeatureStore

store = FeatureStore(repo_path="feature_repo")
store_with_custom_yaml = FeatureStore(
    repo_path="feature_repo",
    fs_yaml_file=Path("feature_repo/custom_feature_store.yaml"),
)
```

Rules:

- `repo_path` defaults to the current working directory when omitted.
- `fs_yaml_file` overrides the default `feature_store.yaml` lookup under `repo_path`.
- Do not pass both `config` and `fs_yaml_file`; Feast raises `ValueError("You cannot specify both fs_yaml_file and config.")`.
- Use `FeatureStore(config=repo_config)` only when code already owns a complete `RepoConfig` object.

## Local Provider Behavior

For a local repo, Feast can:

- Read local Parquet data sources.
- Perform historical retrieval using local execution.
- Serve online values from SQLite after materialization.
- Keep registry metadata in a local file such as `data/registry.db`.

Keep local workflows safe by using relative paths and creating the `data/` directory before commands that write registry or online-store files:

```bash
mkdir -p feature_repo/data
python scripts/feature_repo_doctor.py feature_repo
feast -c feature_repo plan --skip-source-validation
```

## .feastignore Patterns

Example `.feastignore`:

```text
venv
scripts/*.py
notebooks/**/*.py
**/__pycache__
```

Feast reads `.feastignore`, strips comments, and expands file or directory patterns. Matching directories exclude Python files under them. Use it when a repo includes utility Python files that execute side effects or are not Feast definitions.
