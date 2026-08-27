# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the Waymo Open Dataset repository. If the current repository commit, dirty state, package version, or major evidence paths differ from this snapshot, refresh the repo skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T16:20:17Z",
  "repository": {
    "name": "waymo-open-dataset",
    "remote_url": "https://github.com/waymo-research/waymo-open-dataset.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "99a4cb3ff07e2fe06c2ce73da001f850f628e45a",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "waymo-open-dataset-tf-2-12-0",
      "version": "1.6.7",
      "import_names": ["waymo_open_dataset"]
    }
  ],
  "evidence": {
    "source_roots": ["src/waymo_open_dataset"],
    "docs": ["README.md", "docs"],
    "examples": ["tutorial"],
    "tests": ["src/waymo_open_dataset/**/*_test.py", "src/waymo_open_dataset/**/*_test.cc"],
    "configs": ["src/WORKSPACE", "src/.bazelrc", "src/.bazelversion", "src/waymo_open_dataset/requirements.in", "src/waymo_open_dataset/requirements.txt"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the snapshot commit, treat the skill as potentially stale.
- If package metadata changes distribution name, version, TensorFlow line, or public modules, refresh the skill.
- If a future wheel packages the latency module or changes optional Deeplab2/camera-op dependencies, refresh `latency-submissions` and `camera-and-segmentation`.
- If V2 component tags, metric wrapper signatures, or sim-agent challenge configs change, refresh the owning sub-skills.
