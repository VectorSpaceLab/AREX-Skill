<!-- SPDX-License-Identifier: Apache-2.0 -->

# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an Apache Airflow checkout. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-23T00:00:00Z",
  "repository": {
    "name": "apache-airflow",
    "remote_url": "https://github.com/apache/airflow",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "4824280c895ff40b1d0f304b26e5917ab9753be1",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {"name": "apache-airflow", "version": "3.3.0", "import_names": ["airflow"]},
    {"name": "apache-airflow-core", "version": "3.3.0", "import_names": ["airflow"]},
    {"name": "apache-airflow-task-sdk", "version": "1.3.0", "import_names": ["airflow.sdk"]},
    {"name": "apache-airflow-ctl", "version": "0.1.5", "import_names": ["airflowctl"]},
    {"name": "apache-airflow-providers-standard", "version": "1.15.0", "import_names": ["airflow.providers.standard"]}
  ],
  "evidence": {
    "source_roots": ["airflow-core/src/airflow", "task-sdk/src/airflow/sdk", "airflow-ctl/src/airflowctl", "providers/standard/src/airflow/providers/standard", "chart/templates", "dev/breeze/src"],
    "docs": ["README.md", "airflow-core/docs", "task-sdk/docs", "airflow-ctl/docs", "chart/docs", "docker-stack-docs", "contributing-docs"],
    "examples": ["airflow-core/src/airflow/example_dags", "providers/standard/src/airflow/providers/standard/example_dags"],
    "tests": ["airflow-core/tests/unit", "task-sdk/tests", "airflow-ctl/tests", "providers/standard/tests", "chart/tests/helm_tests", "dev/breeze/tests", "scripts/tests"],
    "configs": ["pyproject.toml", "airflow-core/pyproject.toml", "task-sdk/pyproject.toml", "airflow-ctl/pyproject.toml", "providers/standard/pyproject.toml", "chart/values.yaml", "AGENTS.md"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ, run `refresh-repo-skill`.
- If Airflow package metadata, public CLI groups, provider package conventions, chart values, or contribution/testing rules changed, run `refresh-repo-skill`.
