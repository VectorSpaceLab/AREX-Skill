# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package shape, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T17:08:04Z",
  "repository": {
    "name": "multidiffusion-upscaler-for-automatic1111",
    "remote_url": "https://github.com/pkuliyi2015/multidiffusion-upscaler-for-automatic1111.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "22798f6822bc9c8a905b51da8954ee313b973331",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/ (untracked repo-local production artifacts/logs and generated skill output)"
    ]
  },
  "packages": [
    {
      "name": "multidiffusion-upscaler-for-automatic1111",
      "version": null,
      "import_names": ["tile_methods", "tile_utils"],
      "distribution": "none; AUTOMATIC1111 WebUI extension"
    }
  ],
  "evidence": {
    "source_roots": ["scripts", "tile_methods", "tile_utils", "javascript"],
    "docs": ["README.md"],
    "examples": [],
    "tests": [],
    "configs": ["runtime-generated region_configs/ is ignored and not present in this checkout"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If WebUI extension entrypoints, panel names, sampler hooks, or utility schemas changed, refresh even if the high-level README looks similar.
- If a future checkout adds package metadata, requirements, tests, examples, or docs, refresh to add install/runtime verification that was not available in this snapshot.
- If dirty paths include tracked source changes outside repo-local `skills/` artifacts, refresh before relying on implementation details.
