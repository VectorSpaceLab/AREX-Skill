# Repository Provenance

Read this before deciding whether the runtime skill matches a checkout. If the
commit, dirty state, package version, public entry points, or major evidence
paths differ, run a repo-skill refresh.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T00:00:00Z",
  "repository": {
    "name": "Fiona",
    "remote_url": "https://github.com/Toblerity/Fiona",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "ec9768a9389530a0570446e3c34ae91448d28cf4",
    "working_tree": "clean-at-analysis; generated skill files are outside source baseline",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "fiona",
      "version": "2.0.0.dev0",
      "import_names": ["fiona"]
    }
  ],
  "evidence": {
    "source_roots": ["fiona"],
    "docs": ["README.rst", "docs"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "setup.py", "environment.yml", "requirements.txt"]
  }
}
```

## Refresh check

- Compare the current `git rev-parse HEAD` with the recorded commit.
- Compare current dirty paths and public package metadata with this snapshot.
- Recheck the `fio` entry point and major modules (`collection`, `io`, `model`,
  `crs`, `transform`, `env`, `session`, and `fio`) when source APIs change.
- The source snapshot uses GDAL 3.4.3 for private inspection, but that runtime
  detail is evidence, not a requirement that every user reproduce the same
  binary build. Follow the installed Fiona release's documented compatibility.
