# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a DocsGPT checkout. If the commit, dirty state, application version, public entry points, or major evidence paths differ, refresh the repo skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-28T00:55:00Z",
  "repository": {
    "name": "DocsGPT",
    "remote_url": "https://github.com/arc53/DocsGPT.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "ff5bc01d20430b52d9028f71ebcaaa34c1a6b8e0",
    "working_tree": "clean-before-generated-skill-output",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "DocsGPT backend application",
      "version": "0.18.0",
      "import_names": ["application"],
      "distribution_metadata": null
    },
    {
      "name": "DocsGPT frontend",
      "version": "0.0.0",
      "import_names": []
    },
    {
      "name": "docsgpt React widget",
      "version": "0.1.11",
      "import_names": []
    }
  ],
  "evidence": {
    "source_roots": ["application", "frontend/src", "extensions"],
    "docs": ["README.md", "CONTRIBUTING.md", "AGENTS.md", "docs/content", "docs/runbooks"],
    "examples": ["application/seed/config", "scripts/e2e/mock_llm_fixtures"],
    "tests": ["tests"],
    "configs": [".env-template", "application/core/settings.py", "application/core/models", "deployment", "frontend/package.json"],
    "scripts": ["scripts"]
  }
}
```

## Evidence interpretation

- DocsGPT is an application repository, not a Python distribution with `pyproject.toml`, `setup.py`, or `setup.cfg`. Source-development imports use the top-level `application` package.
- Public behavior was confirmed from source, docs, tests, route inspection, Pydantic schemas, and isolated runtime import/signature checks.
- Exact registry keys at this snapshot: agents `classic`, `react`, `agentic`, `research`, `workflow`; chunkers `classic_chunk`, `recursive`, `markdown`, `parent_child`, `semantic`; retrievers `classic`, `default`, `hybrid`, `graphrag`; remote loaders `url`, `sitemap`, `crawler`, `reddit`, `github`, `s3`; connectors `google_drive`, `share_point`, `confluence`; vector stores `faiss`, `elasticsearch`, `mongodb`, `qdrant`, `milvus`, `pgvector`.

## Refresh check

- Compare `git rev-parse HEAD` with the snapshot commit.
- Compare `application.version.get_version()` and public endpoint/registry surfaces.
- Refresh when settings, source config, workflow schemas, routes, model catalog schema, parser formats, retrievers, vector stores, tools, deployment topology, or agent portability change.
- A dirty source checkout requires reviewing relative changed paths; never put machine paths or secrets into refreshed provenance.
