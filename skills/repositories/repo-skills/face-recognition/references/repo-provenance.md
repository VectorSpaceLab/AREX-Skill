# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, package version, public APIs, CLI entry
points, evidence paths, or dependency behavior differ from this snapshot, run
`refresh-repo-skill`.

The source snapshot was captured before generated skill files and review
artifacts were written under `skills/`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T06:17:34Z",
  "repository": {
    "name": "face_recognition",
    "remote_url": "https://github.com/ageitgey/face_recognition.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "9f3061aaeed9a8756d2c970f5dfe066617a8281d",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "face_recognition",
      "version": "1.4.0",
      "import_names": ["face_recognition"]
    }
  ],
  "evidence": {
    "source_roots": ["face_recognition"],
    "docs": [
      "README.md",
      "README.rst",
      "docs/installation.rst",
      "docs/usage.rst",
      "docs/face_recognition.rst",
      "docker/README.md"
    ],
    "examples": ["examples"],
    "tests": ["tests/test_face_recognition.py", "tests/test_images"],
    "package_metadata": [
      "setup.py",
      "setup.cfg",
      "pyproject.toml",
      "requirements.txt",
      "requirements_dev.txt",
      "tox.ini",
      ".github/workflows/main.yml",
      "Makefile"
    ],
    "deployment": ["Dockerfile", "Dockerfile.gpu", "docker-compose.yml", "docker"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If package metadata, public entry points, exported function signatures, CLI
  options, or bundled model dependency behavior changed even on the same commit,
  refresh the skill.
- If examples/docs/tests were reorganized or renamed, refresh the evidence map
  and source-script inventory.
- Generated `skills/disco/face-recognition/` and `skills/tests/face-recognition/`
  files are outputs of this construction run, not source evidence changes.
