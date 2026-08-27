# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
`rank_bm25` repository. If the commit, dirty state, package metadata, or public
API evidence differs, run the repository-skill refresh workflow before relying
on the graph for a changed capability.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-23T07:22:37Z",
  "repository": {
    "name": "rank_bm25",
    "remote_url": "https://github.com/dorianbrown/rank_bm25",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "47aa3ddf8dc1ebeb7ef4e65f2b4536af44594099",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "rank_bm25",
      "version": null,
      "import_names": ["rank_bm25"]
    },
    {
      "name": "numpy",
      "version": null,
      "import_names": ["numpy"]
    }
  ],
  "evidence": {
    "source_roots": ["rank_bm25.py"],
    "docs": ["README.md"],
    "examples": ["README.md usage blocks"],
    "tests": ["tests/test_loading.py"],
    "configs": ["setup.py", "requirements.txt", "version.py"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `47aa3ddf8dc1ebeb7ef4e65f2b4536af44594099`, treat this skill as potentially stale.
- If the checkout becomes dirty, or its changed paths differ from the clean baseline above, refresh before making source-level claims.
- Refresh if distribution metadata, constructor signatures, public class availability, tokenization behavior, or the implemented algorithm set changes.
- The checkout has no exact numeric Git tag at this baseline, so `version: null`
  is intentional; do not interpret the private inspection workaround's
  temporary version as the public release version.
