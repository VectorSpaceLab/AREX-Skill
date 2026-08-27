# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a PyRIT checkout. If the current commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T12:19:51Z",
  "repository": {
    "name": "PyRIT",
    "remote_url": "https://github.com/microsoft/PyRIT.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "f618c27d1274da004ee0456fb4a93cc3d561369b",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "pyrit",
      "version": "1.1.0.dev0",
      "import_names": [
        "pyrit"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "pyrit"
    ],
    "docs": [
      "README.md",
      "doc/getting_started",
      "doc/code",
      "doc/scanner",
      "doc/gui"
    ],
    "examples": [
      "doc/code",
      "doc/scanner"
    ],
    "tests": [
      "tests/unit",
      "tests/integration selected as candidate evidence"
    ],
    "configs": [
      "pyproject.toml",
      ".pyrit_conf_example",
      ".env_example",
      ".env_local_example"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale.
- If the working-tree dirty paths differ materially from this snapshot, refresh the skill.
- If public package metadata, console entry points, or major PyRIT component APIs changed, refresh the skill even on the same commit.
