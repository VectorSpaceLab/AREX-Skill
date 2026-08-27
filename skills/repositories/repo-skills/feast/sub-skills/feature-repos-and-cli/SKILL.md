---
name: feature-repos-and-cli
description: "Create and operate Feast feature repositories with
  feature_store.yaml, feast init/apply/plan/listing/teardown, registry paths,
  CLI flags, and local provider workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Feast Feature Repos and CLI

Use this sub-skill when the user asks to create, validate, configure, inspect, apply, plan, list, or tear down a Feast feature repository, especially with `feature_store.yaml`, `feast init`, `feast apply`, registry files, `FeatureStore(repo_path=...)`, `--chdir`, or `--feature-store-yaml`.

## Route First

- Use this sub-skill for repository layout, configuration discovery, CLI command selection, local provider setup, registry paths, project naming, `FeatureStore(repo_path=...)`, object `apply`/`plan`, listing commands, and safe teardown guidance.
- Route feature object modeling details such as `Entity`, `Field`, `FeatureView`, `FeatureService`, data sources, and transformations to `../feature-definitions/SKILL.md`.
- Route historical/online retrieval, materialization windows, push ingestion, and saved datasets to `../retrieval-and-materialization/SKILL.md`.
- Route feature server, offline server, registry server, remote stores, TLS, and auth serving topology to `../servers-and-remote/SKILL.md`.
- Route contributor setup, Feast source-tree tests, linting, mypy, protos, and PR workflow to `../repo-development/SKILL.md`.

## Fast Path

1. Confirm Feast is available: `feast version` or `python -c "import feast; print(feast.__version__)"`.
2. Create a repo: `feast init my_project`, then work from `my_project/feature_repo` unless using `--repo-path`.
3. Inspect `feature_store.yaml`; for local development prefer `provider: local`, a file registry such as `data/registry.db`, and a SQLite online store.
4. Validate config safely before running mutating commands: `python scripts/feature_repo_doctor.py /path/to/feature_repo`.
5. Preview changes with `feast -c /path/to/feature_repo plan --skip-source-validation` before `feast -c /path/to/feature_repo apply`.
6. List or inspect registered objects with `feast ... entities list`, `feature-views list`, `feature-services list`, and `registry-dump`.

## References

- `references/cli-reference.md` for CLI command routing, global flags, listing commands, and destructive command warnings.
- `references/configuration.md` for `feature_store.yaml`, registry path, project naming, and local provider configuration.
- `references/workflows.md` for common init, safe plan/apply, custom config path, and Python API workflows.
- `references/troubleshooting.md` for install/import, config, CLI/API misuse, credentials, and workflow-specific failures.
- `scripts/feature_repo_doctor.py` for safe local validation that does not run `feast apply`, import repo Python modules, contact services, or delete resources.
