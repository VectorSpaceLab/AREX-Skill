# Repository Provenance

## Purpose

Read this before deciding whether the operating graph is current for a ClawBio
checkout. If the commit, package version, dirty state, catalog, or public entry
points differ, run a repo-skill refresh rather than assuming the detailed
routes still apply.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T00:00:00Z",
  "repository": {
    "name": "ClawBio",
    "remote_url": "https://github.com/ClawBio/ClawBio",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "866be13215ed2b2eb0b712372b9fe8d3f1d664d1",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "clawbio",
      "version": "0.6.1",
      "import_names": ["clawbio"]
    }
  ],
  "evidence": {
    "source_roots": ["clawbio", "clawbio.py"],
    "docs": ["README.md", "CLAUDE.md", "docs", "commands", "CONTRIBUTING.md", "SECURITY-AUDIT.md"],
    "examples": ["examples", "demo"],
    "tests": ["clawbio/tests", "tests", "bot/tests", "robotary/tests"],
    "configs": ["pyproject.toml", "pytest.ini", "templates", "skills/catalog.json"]
  }
}
```

## Refresh check

- Compare `git rev-parse HEAD` with the recorded commit.
- If the current checkout is dirty or its changed paths differ from the
  snapshot, refresh before making detailed claims.
- Recheck the distribution version and the `clawbio` console entry point.
- Regenerate or inspect the catalog when skill metadata or registration changes.
- Large reference data, generated reports, caches, images, slides, and review
  artifacts were evidence exclusions; their presence does not by itself make
  this graph stale.
