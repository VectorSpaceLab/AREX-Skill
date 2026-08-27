# Repository Provenance

## Purpose

Read this before deciding whether the generated skill matches a checkout of
pykitti. If the commit, package version, dirty state, public entry points, or
major evidence paths differ, run a repository-skill refresh before relying on
these instructions.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T18:04:42Z",
  "repository": {
    "name": "pykitti",
    "remote_url": "https://github.com/utiasSTARS/pykitti.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "de337234413f4b9d192da7e3d3fc28de5281c748",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "pykitti",
      "version": "0.3.1",
      "import_names": ["pykitti", "pykitti.raw", "pykitti.odometry", "pykitti.tracking", "pykitti.utils"]
    }
  ],
  "evidence": {
    "source_roots": ["pykitti"],
    "docs": ["README.md"],
    "examples": ["demos"],
    "tests": [],
    "configs": ["setup.py", "setup.cfg"]
  }
}
```

## Refresh check

- Compare `git rev-parse HEAD` with the recorded commit.
- If the checkout is clean or its dirty paths differ from this snapshot, treat
  the skill as potentially stale; generated `skills/` artifacts were present
  while this skill was constructed.
- Recheck `setup.py`, public exports, and the `pykitti/` source root if package
  metadata or entry points changed.
- The source repository contains no native test suite; the demos are evidence
  and data-dependent candidates, not runtime dependencies of this skill.
