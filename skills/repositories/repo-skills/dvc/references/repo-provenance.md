# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the DVC repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-23T00:00:00Z",
  "repository": {
    "name": "dvc",
    "remote_url": "https://github.com/treeverse/dvc",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "8131c32c336b2f0cb47cb8782141d899a4876b8e",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "dvc",
      "version": "0.1.dev1+g8131c32c3",
      "import_names": [
        "dvc"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "dvc"
    ],
    "docs": [
      "README.rst",
      "CONTRIBUTING.md"
    ],
    "examples": [],
    "tests": [
      "tests/func",
      "tests/unit",
      "tests/integration",
      "tests/remotes"
    ],
    "configs": [
      "pyproject.toml",
      ".pre-commit-config.yaml",
      ".pre-commit-hooks.yaml"
    ],
    "selected_source_areas": [
      "dvc/api",
      "dvc/cli",
      "dvc/commands",
      "dvc/config_schema.py",
      "dvc/fs",
      "dvc/repo",
      "dvc/schema.py",
      "dvc/stage",
      "dvc/testing"
    ],
    "excluded_areas": [
      ".dvc",
      ".github",
      "build outputs and caches",
      "optional cloud backend packages not needed for core inspection",
      "skills/tests review artifacts"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has non-skill changes that are not represented in `dirty_paths`, run `refresh-repo-skill`.
- If package metadata, console entry points, command families, public `dvc.api` signatures, or optional dependency extras changed, run `refresh-repo-skill`.
- If DVC test layout or pytest markers changed and the task is repo maintenance, refresh the `repo-development` sub-skill.
