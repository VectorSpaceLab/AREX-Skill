# Repository Provenance

## Purpose

Read this before deciding whether the BiSheng repo skill is current for a checkout. If the current repository commit, tag, package version, architecture documents, package metadata, or major source layout differ from this snapshot, refresh the repo skill before relying on it for implementation guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T16:20:14Z",
  "repository": {
    "name": "bisheng",
    "remote_url": "https://github.com/dataelement/bisheng.git",
    "vcs": "git",
    "branch": "main",
    "tag": "v2.6.0-fix",
    "commit": "a3788115d71f4b5888a34fbe7e1f0f3f9f13784c",
    "working_tree": "clean-source-snapshot-before-generated-skill-output",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "backend",
      "version": "2.6.0",
      "import_names": ["bisheng", "bisheng_langchain"]
    },
    {
      "name": "bisheng",
      "version": "2.6.0",
      "import_names": ["platform frontend app"]
    },
    {
      "name": "bishengchat",
      "version": "2.6.0",
      "import_names": ["client frontend app"]
    }
  ],
  "evidence": {
    "source_roots": [
      "src/backend/bisheng",
      "src/backend/bisheng_langchain",
      "src/frontend/platform/src",
      "src/frontend/client/src"
    ],
    "docs": [
      "README.md",
      "README_CN.md",
      "docs/README.md",
      "docs/constitution.md",
      "docs/architecture"
    ],
    "metadata": [
      "src/backend/pyproject.toml",
      "src/backend/uv.lock",
      "src/frontend/platform/package.json",
      "src/frontend/client/package.json"
    ],
    "tests": [
      "src/backend/test",
      "src/frontend/platform/src/test",
      "src/frontend/client/src/**/*.test.*"
    ],
    "scripts": [
      "scripts",
      "tools",
      "src/backend/scripts",
      "docker"
    ],
    "agent_rules": [
      "AGENTS.md",
      "src/backend/AGENTS.md",
      "src/frontend/platform/AGENTS.md",
      "src/frontend/client/AGENTS.md",
      "src/backend/scripts/AGENTS.md"
    ]
  },
  "environment_preparation": {
    "status": "ok-for-read-only-inspection",
    "manager": "conda",
    "python": "3.11.15",
    "notes": [
      "Python source importability was verified by adding the backend source root to an isolated inspection prefix because editable package metadata rejects the non-SPDX license string under current setuptools.",
      "No repository-native tests or examples were executed during construction; native verification is represented by safe parser/help checks for bundled helpers."
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, refresh the skill.
- If `src/backend/pyproject.toml`, either frontend `package.json`, root or subproject `AGENTS.md`, `docs/constitution.md`, or `docs/architecture/*` changed, refresh the relevant sub-skill or the whole graph.
- If BiSheng changes its backend package name, import names, frontend app split, router metadata, or deployment process, refresh this skill before using commands or routing guidance.
