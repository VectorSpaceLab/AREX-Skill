# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T22:15:55Z",
  "repository": {
    "name": "robosuite",
    "remote_url": "https://github.com/ARISE-Initiative/robosuite.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "5ce6643f3092639d08f7b0f90ed1c6a84f50552c",
    "working_tree": "dirty-generated-skill-artifacts-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "robosuite",
      "version": "1.5.2",
      "import_names": ["robosuite"]
    }
  ],
  "evidence": {
    "source_roots": [
      "robosuite"
    ],
    "docs": [
      "README.md",
      "docs/basicusage.md",
      "docs/modules",
      "docs/tutorials",
      "docs/algorithms"
    ],
    "examples": [
      "robosuite/demos",
      "robosuite/examples/third_party_controller"
    ],
    "tests": [
      "tests/test_environments",
      "tests/test_controllers",
      "tests/test_robots",
      "tests/test_grippers",
      "tests/test_renderers"
    ],
    "configs": [
      "robosuite/controllers/config",
      "requirements.txt",
      "requirements-extra.txt",
      "setup.py",
      "pyproject.toml"
    ],
    "scripts": [
      "robosuite/scripts"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has non-skill source changes, or if generated skill artifacts are no longer the only dirty paths, run `refresh-repo-skill` before relying on this skill for current behavior.
- If package metadata, public registries, controller config formats, wrappers, scripts, or public entry points changed even on the same commit, run `refresh-repo-skill`.
