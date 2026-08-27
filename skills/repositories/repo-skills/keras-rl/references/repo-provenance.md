# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of keras-rl. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T08:51:42Z",
  "repository": {
    "name": "keras-rl",
    "remote_url": "https://github.com/keras-rl/keras-rl.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "216c3145f3dc4d17877be26ca2185ce7db462bad",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "keras-rl",
      "version": "0.4.2",
      "import_names": ["rl"]
    }
  ],
  "evidence": {
    "source_roots": ["rl/"],
    "docs": ["README.md", "docs/sources/"],
    "examples": ["examples/"],
    "tests": ["tests/", "utils/gym/"],
    "metadata": ["setup.py", "setup.cfg", "pytest.ini", ".travis.yml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the dirty paths differ in package-relevant files, run `refresh-repo-skill`.
- If package metadata, public imports, example workflows, or tests changed even on the same commit, run `refresh-repo-skill`.
- If the task uses a modern Keras/TensorFlow/Gym stack not covered by this legacy snapshot, verify compatibility with the bundled smoke helpers before relying on runtime behavior.
