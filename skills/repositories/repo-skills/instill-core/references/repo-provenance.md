# Repository Provenance

## Purpose

Read this before deciding whether the skill is current for a checkout of Instill Core. If the current commit, branch, chart version, release metadata, or dirty paths differ from this snapshot, refresh the skill before relying on it.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T11:16:04Z",
  "repository": {
    "name": "instill-core",
    "remote_url": "https://github.com/instill-ai/instill-core.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "b9976c41f47b076991463725a963ee3bfc446030",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/disco/instill-core",
      "skills/instill-core.log",
      "skills/tests/instill-core"
    ]
  },
  "packages": [
    {
      "name": "instill-core",
      "version": "0.58.1",
      "import_names": [],
      "source": "release-please/manifest.json"
    },
    {
      "name": "core-helm-chart",
      "version": "0.1.75",
      "app_version": "0.58.1",
      "import_names": [],
      "source": "charts/core/Chart.yaml"
    }
  ],
  "evidence": {
    "source_roots": [
      "README.md",
      "AGENTS.md",
      "Makefile",
      "Makefile.helm",
      "Makefile.helper",
      "docker-compose.yml",
      "docker-compose-dev.yml",
      "docker-compose-nvidia.yml",
      "docker-compose-observe.yml",
      "charts/core",
      "configs/compose",
      "configs/helm",
      "integration-test",
      "schema",
      ".github/workflows",
      "release-please"
    ],
    "docs": [
      "README.md",
      "AGENTS.md",
      ".github/CONTRIBUTING.md",
      "charts/core/README.md"
    ],
    "examples": ["integration-test/models"],
    "tests": ["integration-test"],
    "configs": ["configs/compose", "configs/helm", "charts/core"]
  }
}
```

## Refresh check

- If the checkout commit changes, treat the skill as potentially stale.
- If the dirty paths change materially, refresh the skill.
- If the release metadata or Helm chart version changes, refresh the skill.
