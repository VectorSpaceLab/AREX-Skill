# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, public API
surface, or major evidence paths differ from this snapshot, run the repo-skill
refresh workflow.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-10T13:22:54Z",
  "repository": {
    "name": "giskard-oss",
    "remote_url": "https://github.com/Giskard-AI/giskard-oss.git",
    "vcs": "git",
    "branch": "main",
    "tag": "giskard-scan/v1.0.0b4",
    "commit": "b6b8403ffa88d4a2e135aed5f850bc73ed7ac814",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/ (untracked generated skill and review artifacts present during construction)"
    ]
  },
  "packages": [
    {
      "name": "giskard",
      "version": "3.0.0b1",
      "import_names": ["giskard.core", "giskard.llm", "giskard.agents", "giskard.checks", "giskard.scan"]
    },
    {
      "name": "giskard-core",
      "version": "1.0.1b6",
      "import_names": ["giskard.core"]
    },
    {
      "name": "giskard-llm",
      "version": "1.0.0b6",
      "import_names": ["giskard.llm"]
    },
    {
      "name": "giskard-agents",
      "version": "1.0.2b6",
      "import_names": ["giskard.agents"]
    },
    {
      "name": "giskard-checks",
      "version": "1.0.2b6",
      "import_names": ["giskard.checks"]
    },
    {
      "name": "giskard-scan",
      "version": "1.0.0b4",
      "import_names": ["giskard.scan"]
    }
  ],
  "evidence": {
    "source_roots": [
      "giskard_pypi_shim/",
      "libs/giskard-core/src/giskard/core/",
      "libs/giskard-llm/src/giskard/llm/",
      "libs/giskard-agents/src/giskard/agents/",
      "libs/giskard-checks/src/giskard/checks/",
      "libs/giskard-scan/src/giskard/scan/"
    ],
    "docs": [
      "README.md",
      "libs/giskard-core/README.md",
      "libs/giskard-llm/README.md",
      "libs/giskard-llm/docs/design.md",
      "libs/giskard-agents/README.md",
      "libs/giskard-checks/README.md",
      "libs/giskard-scan/README.md"
    ],
    "tests": [
      "libs/giskard-core/tests/",
      "libs/giskard-llm/tests/",
      "libs/giskard-agents/tests/",
      "libs/giskard-checks/tests/",
      "libs/giskard-scan/tests/"
    ],
    "configs": [
      "pyproject.toml",
      "libs/giskard-core/pyproject.toml",
      "libs/giskard-llm/pyproject.toml",
      "libs/giskard-agents/pyproject.toml",
      "libs/giskard-checks/pyproject.toml",
      "libs/giskard-scan/pyproject.toml",
      "Makefile",
      "AGENTS.md"
    ],
    "existing_agent_guidance": [
      ".cursor/skills/",
      ".claude/skills/",
      ".cursor/rules/",
      ".claude/CLAUDE.md"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the stored commit, treat this skill as
  potentially stale.
- If the current working tree is clean but the snapshot was dirty, or dirty
  paths differ materially, verify whether generated skill files or source files
  changed and refresh if needed.
- If package metadata, optional extras, provider prefixes, public imports,
  signatures, or native test behavior changed, refresh the affected sub-skills.
- If a task depends on optional live providers, third-party scanners, private
  integrations, or network datasets, verify those capabilities separately; this
  provenance records only the base CPU package-inspection baseline.
