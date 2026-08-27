# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-23T00:00:00Z",
  "repository": {
    "name": "nni",
    "remote_url": "https://github.com/microsoft/nni",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "767ed7f22e1e588ce76cbbecb6c6a4a76a309805",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "nni",
      "version": "999.dev0",
      "import_names": [
        "nni",
        "nni_assets"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "nni",
      "nni_assets"
    ],
    "metadata": [
      "setup.py",
      "dependencies/required.txt",
      "dependencies/required_extra.txt"
    ],
    "docs": [
      "README.md",
      "docs/source"
    ],
    "examples": [
      "examples"
    ],
    "tests": [
      "test/ut",
      "test/algo",
      "test/training_service/config"
    ],
    "configs": [
      "nni/runtime/default_config",
      "examples/trials",
      "test/training_service/config"
    ],
    "excluded": [
      "ts",
      "pipelines",
      ".github",
      "docs/_removed"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and dirty paths differ, run `refresh-repo-skill`.
- If `setup.py`, `dependencies/`, `nni/`, `docs/source/`, `examples/`, or the public `nnictl` entry point changed, refresh before relying on detailed API and workflow guidance.
- If package metadata or optional dependency boundaries changed without a commit change, refresh the skill.
