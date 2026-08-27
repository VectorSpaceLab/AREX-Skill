# Repository Provenance

## Purpose

Read this before deciding whether the skill matches a checkout of
`lucidrains/alphafold2`. If the commit, package version, public signatures, or
major evidence paths differ, use the refresh workflow before relying on the
operating guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T17:47:05Z",
  "repository": {
    "name": "alphafold2",
    "remote_url": "https://github.com/lucidrains/alphafold2",
    "vcs": "git",
    "branch": "main",
    "tag": "v0.4.32",
    "commit": "931466e487e1be87d1182b17ed4ecfac9e70948d",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "alphafold2-pytorch",
      "version": "0.4.32",
      "import_names": ["alphafold2_pytorch"]
    }
  ],
  "evidence": {
    "source_roots": ["alphafold2_pytorch"],
    "docs": ["README.md"],
    "examples": ["notebooks", "scripts/refinement.py"],
    "tests": ["tests"],
    "configs": ["setup.py", "setup.cfg"]
  }
}
```

The dirty state reflects the generated skill and private review artifacts;
those artifacts are not source-package evidence.

## Refresh checks

- If `git rev-parse HEAD` differs from the recorded commit, treat this graph
  as potentially stale.
- If the current package metadata or public `Alphafold2` signatures differ,
  refresh even when the commit is unchanged.
- If source/README drift is resolved in a later release, update the relevant
  sub-skill references rather than carrying old compatibility warnings.
- The snapshot intentionally records only relative evidence paths and public
  repository metadata; it does not record an inspection interpreter,
  environment prefix, cache, or checkout path.
