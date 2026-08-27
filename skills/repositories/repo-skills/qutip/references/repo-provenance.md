# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of QuTiP.
If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T14:56:37Z",
  "repository": {
    "name": "qutip",
    "remote_url": "https://github.com/qutip/qutip.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "8d9e2406c5a05e374b10cc0a980b83a5ff4f6ab7",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "qutip",
      "version": "5.4.0.dev0+8d9e240",
      "import_names": ["qutip"]
    }
  ],
  "evidence": {
    "metadata": ["pyproject.toml", "setup.py", "requirements.txt", "VERSION"],
    "docs": ["README.md", "doc/installation.rst", "doc/guide/", "doc/apidoc/"],
    "source_roots": ["qutip/", "qutip/core/", "qutip/solver/", "qutip/piqs/"],
    "tests": ["qutip/tests/"],
    "configs": [".github/workflows/tests.yml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and the dirty paths differ materially from this snapshot, run `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit, run `refresh-repo-skill`.
