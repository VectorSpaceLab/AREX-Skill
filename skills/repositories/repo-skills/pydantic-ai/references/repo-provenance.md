# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-22T00:00:00Z",
  "repository": {
    "name": "pydantic-ai",
    "remote_url": "https://github.com/pydantic/pydantic-ai",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "88fb4e34eb24bb39d08a900bfe5f631d7df49484",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "pydantic-ai",
      "version": "0.0.1.dev1+88fb4e3",
      "import_names": ["pydantic_ai"]
    },
    {
      "name": "pydantic-ai-slim",
      "version": "0.0.1.dev1+88fb4e3",
      "import_names": ["pydantic_ai"]
    },
    {
      "name": "pydantic-graph",
      "version": "0.0.1.dev1+88fb4e3",
      "import_names": ["pydantic_graph"]
    },
    {
      "name": "pydantic-evals",
      "version": "0.0.1.dev1+88fb4e3",
      "import_names": ["pydantic_evals"]
    },
    {
      "name": "clai",
      "version": "0.0.1.dev1+88fb4e3",
      "import_names": ["clai"]
    }
  ],
  "evidence": {
    "source_roots": [
      "pydantic_ai_slim/pydantic_ai",
      "pydantic_graph/pydantic_graph",
      "pydantic_evals/pydantic_evals",
      "clai/clai",
      "examples/pydantic_ai_examples"
    ],
    "docs": [
      "README.md",
      "docs",
      "mkdocs.yml",
      "agent_docs"
    ],
    "examples": [
      "examples"
    ],
    "tests": [
      "tests"
    ],
    "configs": [
      "pyproject.toml",
      "pydantic_ai_slim/pyproject.toml",
      "pydantic_graph/pyproject.toml",
      "pydantic_evals/pyproject.toml",
      "clai/pyproject.toml",
      "examples/pyproject.toml",
      "Makefile",
      ".pre-commit-config.yaml"
    ],
    "existing_skills": [
      "pydantic_ai_slim/pydantic_ai/.agents/skills/building-pydantic-ai-agents",
      ".claude/skills"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has dirty paths that change public APIs, docs, examples, tests, package metadata, generated skills, or workflow scripts beyond the recorded `skills/` generation output, run `refresh-repo-skill`.
- If any workspace package changes public entry points, optional extras, CLI behavior, model/provider names, output/message contracts, tool APIs, MCP/capability mechanics, evals/graph APIs, or maintainer workflow rules, refresh the affected sub-skills.
- Do not use local environment paths, editable-install paths, or private inspection environment details as freshness criteria; they are intentionally omitted from public provenance.
