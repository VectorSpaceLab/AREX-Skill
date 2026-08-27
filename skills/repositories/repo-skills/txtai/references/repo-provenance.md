# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of txtai. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-22T16:31:53Z",
  "repository": {
    "name": "txtai",
    "remote_url": "https://github.com/neuml/txtai",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "21e6ab8e6ad5157e01d7adfbfc417d3e0da373a1",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "txtai",
      "version": "9.11.0",
      "import_names": ["txtai"]
    }
  ],
  "evidence": {
    "metadata": ["setup.py", "pyproject.toml"],
    "source_roots": ["src/python/txtai"],
    "docs": [
      "README.md",
      "docs/install.md",
      "docs/faq.md",
      "docs/models.md",
      "docs/embeddings",
      "docs/pipeline",
      "docs/workflow",
      "docs/agent",
      "docs/api",
      "docs/cloud.md",
      "docs/observability.md"
    ],
    "examples": ["examples/*.py", "examples/*.ipynb"],
    "tests": ["test/python"],
    "deployment": ["docker", "Makefile"]
  },
  "generated_skill": {
    "id": "txtai",
    "sub_skills": [
      "embeddings-search",
      "pipelines-and-workflows",
      "agents-and-llm-orchestration",
      "api-and-deployment"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as potentially stale.
- If the current dirty paths differ from the recorded dirty paths, review whether runtime skill content came from uncommitted source changes.
- If `setup.py` or package metadata reports a different txtai version, refresh the skill before relying on API signatures or optional extras.
- If `src/python/txtai`, `docs/embeddings`, `docs/pipeline`, `docs/workflow`, `docs/agent`, `docs/api`, examples, or tests changed substantially, refresh the affected sub-skills.

## Evidence Boundaries

This skill distilled repository source, docs, examples, tests, and deployment files into self-contained references and scripts. Runtime instructions should not depend on the original checkout remaining available.
