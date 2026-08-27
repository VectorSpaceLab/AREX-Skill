# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Operação Serenata de Amor. If the current repo commit, dirty state, package metadata, dependency pins, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T20:09:10Z",
  "repository": {
    "name": "serenata-de-amor",
    "remote_url": "https://github.com/okfn-brasil/serenata-de-amor.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "e7aeba78100b1ec96c2a79a85d6f5dfd1a8adaf7",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["jarbas", "rosie"],
      "note": "The repository has no setup.py or pyproject.toml; Jarbas and Rosie are source-root applications rather than an installable distribution."
    },
    {
      "name": "Django",
      "version": "2.1.7",
      "import_names": ["django"]
    },
    {
      "name": "celery",
      "version": "4.2.1",
      "import_names": ["celery"]
    },
    {
      "name": "djangorestframework",
      "version": "3.9.1",
      "import_names": ["rest_framework"]
    },
    {
      "name": "scikit-learn",
      "version": "0.20.2",
      "import_names": ["sklearn"]
    },
    {
      "name": "serenata-toolbox",
      "version": "15.1.6",
      "import_names": ["serenata_toolbox"]
    }
  ],
  "evidence": {
    "source_roots": [
      "jarbas/",
      "rosie/rosie/"
    ],
    "docs": [
      "README.md",
      "CONTRIBUTING.md",
      "jarbas/README.md",
      "rosie/README.md",
      "contrib/README.md",
      "contrib/update/README.md"
    ],
    "configs": [
      "requirements.txt",
      "requirements-dev.txt",
      "rosie/requirements.txt",
      "docker-compose.yml",
      "docker-compose.override.yml",
      "docker-compose.prod.yml",
      "contrib/.env.sample",
      "package.json",
      "elm-package.json",
      ".travis.yml"
    ],
    "examples_and_data": [
      "contrib/data/README.md",
      "contrib/data/reimbursements_sample.csv",
      "contrib/data/companies_sample.xz",
      "contrib/data/suspicions_sample.xz",
      "rosie/rosie/**/tests/fixtures/"
    ],
    "tests": [
      "jarbas/core/tests/",
      "jarbas/chamber_of_deputies/tests/",
      "jarbas/dashboard/tests/",
      "jarbas/layers/tests/",
      "jarbas/public_admin/tests/",
      "rosie/rosie/**/tests/"
    ],
    "reference_only_or_excluded": [
      "research/src/",
      "research/setup",
      "contrib/update/",
      "contrib/crontab/",
      "contrib/deploy.sh"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as potentially stale.
- If the current working tree has application changes outside generated `skills/` artifacts, refresh before relying on API, command, or classifier details.
- If `requirements.txt`, `rosie/requirements.txt`, `jarbas/settings.py`, URL/view/serializer/queryset/model files, or Rosie classifiers/adapters changed, refresh even on the same commit.
- If the repository becomes an installable Python distribution or updates to modern Django/NumPy/scikit-learn versions, refresh all setup and troubleshooting guidance.
