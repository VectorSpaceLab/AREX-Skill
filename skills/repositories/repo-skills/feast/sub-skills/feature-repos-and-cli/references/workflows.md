# Feature Repository Workflows

## Bootstrap a Local Repo

```bash
feast init my_project
cd my_project/feature_repo
feast configuration
python /path/to/feature-repos-and-cli/scripts/feature_repo_doctor.py .
feast plan --skip-source-validation
feast apply --skip-source-validation
```

Expected signals:

- `feast init` prints `Creating a new Feast repository in ...`.
- `feature_store.yaml` includes `project: my_project`, `provider: local`, a registry path, and SQLite online store config for the default local template.
- `feast configuration` prints the resolved config as YAML.
- `plan` prints registry and infrastructure diff text.
- `apply` prints `Applying changes for project my_project` before applying registry/provider changes.

Use `--skip-source-validation` only when the data source paths or service tables are intentionally unavailable during planning. Remove it before production apply when validation should catch missing sources.

## Create an Empty Repo Safely

```bash
feast init fraud_features --minimal --repo-path /tmp/fraud_features
cd /tmp/fraud_features
cat > feature_store.yaml <<'YAML'
project: fraud_features
registry: data/registry.db
provider: local
online_store:
  type: sqlite
  path: data/online_store.db
entity_key_serialization_version: 3
YAML
mkdir -p data
python /path/to/feature-repos-and-cli/scripts/feature_repo_doctor.py .
```

Then add feature definitions in Python. For object modeling and valid constructors, route to `../../feature-definitions/SKILL.md` before applying.

## Work from Outside the Repo

Prefer `--chdir` when automation runs from a scheduler, monorepo root, or notebook directory:

```bash
REPO=/srv/feature-repos/driver/feature_repo
feast -c "$REPO" configuration
feast -c "$REPO" plan --skip-source-validation
feast -c "$REPO" entities list
```

This avoids relying on the process current directory.

## Use a Custom Config File

Useful for temporary local paths, branch-specific config, or CI smoke checks:

```bash
cp feature_repo/feature_store.yaml feature_repo/feature_store.local.yaml
feast -c feature_repo -f feature_repo/feature_store.local.yaml configuration
feast -c feature_repo -f feature_repo/feature_store.local.yaml plan --skip-source-validation
```

Python equivalent:

```python
from pathlib import Path
from feast import FeatureStore

store = FeatureStore(
    repo_path="feature_repo",
    fs_yaml_file=Path("feature_repo/feature_store.local.yaml"),
)
```

Make sure relative paths in the YAML still resolve as expected for the selected repo path.

## Safe Plan/Apply Sequence

1. Run `python scripts/feature_repo_doctor.py feature_repo` to verify config presence, YAML shape, path hints, and optional Feast import.
2. Run `feast -c feature_repo configuration` to confirm the CLI resolves the intended config.
3. Run `feast -c feature_repo plan --skip-source-validation` when sources may be unavailable, or `feast -c feature_repo plan` when they should be reachable.
4. Review object additions, updates, deletes, and infrastructure changes.
5. Run `feast -c feature_repo apply` only after reviewing the diff and target provider.
6. Run listing commands such as `feature-views list` or `registry-dump` to verify registry state.

Do not treat `plan` as a pure static lint: Feast imports repo Python files and may execute module-level code. Keep side-effect scripts out of the repo parser with `.feastignore`.

## Repair Missing Registry or Data Directory

Symptoms:

- `registry: data/registry.db` exists in YAML but `data/` is missing.
- `feast apply` fails when trying to write local registry or SQLite files.
- Listing commands show no objects because the CLI is reading another registry path.

Safe repair:

```bash
python scripts/feature_repo_doctor.py feature_repo
mkdir -p feature_repo/data
feast -c feature_repo configuration
feast -c feature_repo plan --skip-source-validation
```

If the registry path should be elsewhere, update `feature_store.yaml`, rerun the doctor, and use `registry-dump` to confirm the selected project and registry.

## Apply Objects from Python

Use the CLI for normal repo reconciliation. Use the Python API when code is intentionally applying a known set of objects:

```python
from feast import FeatureStore

store = FeatureStore(repo_path="feature_repo")
store.apply([driver, driver_stats_fv], partial=True)
```

Verified method shape:

```python
FeatureStore.apply(objects, objects_to_delete=None, partial=True,
                   skip_feature_view_validation=False, no_promote=False)
```

Notes:

- `partial=True` applies only the provided objects and does not reconcile the whole repo.
- CLI `feast apply` parses the repository and applies a full desired-state reconciliation.
- Use `store.plan(repo_contents, skip_feature_view_validation=False)` only if code already has a `RepoContents` object; the CLI is simpler for most tasks.

## Before Destructive Cleanup

For `delete` or `teardown`:

```bash
feast -c feature_repo configuration
feast -c feature_repo registry-dump > registry-before.json
feast -c feature_repo plan
# Review project, provider, registry, and object names before continuing.
feast -c feature_repo delete driver_hourly_stats
# or
feast -c feature_repo teardown
```

Never run `teardown` against an unreviewed remote provider or shared registry. Server and remote provider implications belong in `../../servers-and-remote/SKILL.md` and optional backend selection belongs in `../../integrations-and-extensibility/SKILL.md`.
