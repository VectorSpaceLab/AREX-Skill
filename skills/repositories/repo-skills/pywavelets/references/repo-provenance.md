# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of PyWavelets. If the source commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T23:48:24Z",
  "repository": {
    "name": "pywavelets",
    "remote_url": "https://github.com/PyWavelets/pywt.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "bbdf7ebe95f738cfac9b68e4e9c521e87e5a1956",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "PyWavelets",
      "version": "1.8.0.dev0+bbdf7eb",
      "import_names": ["pywt"]
    }
  ],
  "evidence": {
    "source_roots": ["pywt", "pywt/_extensions", "pywt/data"],
    "docs": ["README.rst", "doc/source"],
    "examples": ["demo"],
    "tests": ["pywt/tests"],
    "configs": ["pyproject.toml", "meson.build", "pytest.ini", "tox.ini"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is clean but this snapshot is dirty, or the dirty paths differ, run `refresh-repo-skill`.
- If package metadata, the compiled extension surface, or public entry points changed even on the same commit, run `refresh-repo-skill`.
