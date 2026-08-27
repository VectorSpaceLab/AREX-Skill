# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-29T17:38:56Z",
  "repository": {
    "name": "openfe",
    "remote_url": "https://github.com/OpenFreeEnergy/openfe",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "ab86c842d20c85ea231bbe7ec224582daa56c113",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "openfe",
      "version": "0.0.1.dev1+gab86c842d",
      "import_names": [
        "openfe",
        "openfecli"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "src/openfe",
      "src/openfecli"
    ],
    "docs": [
      "README.md",
      "docs/installation.rst",
      "docs/guide",
      "docs/reference",
      "docs/tutorials",
      "docs/cookbook"
    ],
    "examples": [
      "docs/tutorials",
      "docs/cookbook"
    ],
    "tests": [
      "src/openfe/tests",
      "src/openfecli/tests"
    ],
    "configs": [
      "pyproject.toml",
      "environment.yml",
      "docs/environment.yaml"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has dirty paths outside the generated `skills/` artifact tree, run `refresh-repo-skill` before relying on API or CLI details.
- If public entry points, protocol names, CLI flags, dependency constraints, result schemas, or documented workflow pages changed, run `refresh-repo-skill` even on the same commit.
