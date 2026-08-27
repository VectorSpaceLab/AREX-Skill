# Repository Provenance

## Purpose

Read this before deciding whether this skill matches a checkout of PhiFlow.
If the source commit, dirty state, package version, or major evidence paths have
changed, refresh this skill instead of assuming it is current.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T18:30:10Z",
  "repository": {
    "name": "PhiFlow",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "7569231f0604dce9239afe55f9a671324dbe8f9d",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "phiflow",
      "version": "3.4.0",
      "import_names": ["phi"]
    },
    {
      "name": "phiml",
      "version": "1.16.1",
      "import_names": ["phiml"]
    }
  ],
  "evidence": {
    "source_roots": ["phi"],
    "docs": ["README.md", "docs"],
    "examples": ["examples", "demos"],
    "tests": ["tests"],
    "configs": ["setup.py", "setup.cfg", "MANIFEST.in", ".gitmodules"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the stored commit, refresh the skill.
- If the dirty path set changes materially, refresh the skill.
- If the package version or public entry points change, refresh the skill.
- If the repo has no longer-installed `phiflow` / `phiml` versions matching this
  snapshot, refresh the skill.

## Notes

- The PhiML source is present as a git submodule in this checkout, but the
  runtime skill should rely on the installed `phiml` package rather than the
  original checkout.
- Paths above are relative to the repository root.
