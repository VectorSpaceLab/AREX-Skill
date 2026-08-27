# Repository Provenance

Read this before deciding whether the generated skill still matches a
checkout. If the commit, dirty state, package/API surface, or major evidence
paths differ, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T16:00:00Z",
  "repository": {
    "name": "second.pytorch",
    "remote_url": "https://github.com/traveller59/second.pytorch",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "1b2b58bec1c535a06d7785043664c0fc2ee375f9",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/ (generated runtime skill and review artifacts)",
      "skills/second.pytorch.log (pre-existing interrupted production log)"
    ]
  },
  "packages": [
    {
      "name": "second.pytorch-source",
      "version": null,
      "import_names": ["second", "torchplus"]
    }
  ],
  "evidence": {
    "source_roots": ["second", "torchplus"],
    "docs": ["README.md", "NUSCENES-GUIDE.md", "RELEASE.md"],
    "examples": ["second/simple-inference.ipynb"],
    "tests": ["second/framework/test.py"],
    "configs": ["second/configs", "second/protos"]
  }
}
```

The README labels the project `SECOND for KITTI/NuScenes object detection
(1.6.0 Alpha)`, but the repository has no package metadata. Treat that label as
historical documentation, not as an installed distribution version.

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as
  stale and run `refresh-repo-skill`.
- If the current working tree changes materially, especially under `second/`,
  `torchplus/`, `second/configs/`, or `second/protos/`, refresh before relying
  on signatures or config details.
- If the source adds package metadata, changes Fire entry points, replaces
  spconv APIs, or adds a supported test suite, refresh the compatibility and
  environment claims.
- The generated skill intentionally records a dirty source snapshot because
  the checkout already contained an interrupted production log and this run
  writes the skill under `skills/`. Those artifacts are not runtime package
  dependencies.
