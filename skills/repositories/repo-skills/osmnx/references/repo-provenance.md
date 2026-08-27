# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an OSMnx checkout. If the repository commit, dirty state, package version, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "evidence": {
    "configs": [
      "pyproject.toml",
      "docs/source/installation.rst",
      "docs/source/user-reference.rst"
    ],
    "docs": [
      "README.md",
      "docs/source"
    ],
    "examples": [],
    "source_roots": [
      "osmnx"
    ],
    "tests": [
      "tests/test_osmnx.py",
      "tests/input_data"
    ]
  },
  "generated_at_utc": "2026-08-15T07:13:24Z",
  "packages": [
    {
      "import_names": [
        "osmnx"
      ],
      "name": "osmnx",
      "version": "2.1.1"
    }
  ],
  "repository": {
    "branch": "main",
    "commit": "74e68ce2200b23c04f6ec2a864a6c24859bbf08d",
    "dirty_paths": [
      "skills/"
    ],
    "name": "osmnx",
    "remote_url": "https://github.com/gboeing/osmnx.git",
    "tag": null,
    "vcs": "git",
    "working_tree": "dirty"
  },
  "schema": "disco.repo-provenance.v1"
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the commit above, refresh the skill.
- If the working tree dirty paths differ from the snapshot, refresh the skill.
- If the package version or public module surface changes, refresh the skill even on the same commit.
