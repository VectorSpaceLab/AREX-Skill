# Repository Provenance

Read this before deciding whether the generated operating graph matches a
checkout. If the commit, dirty state, package metadata, or major evidence paths
differ, run a repository-skill refresh rather than assuming the graph is current.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T00:00:00Z",
  "repository": {
    "name": "mmskeleton",
    "remote_url": "https://github.com/open-mmlab/mmskeleton.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "b4c076baa9e02e69b5876c49fa7c509866d902c7",
    "working_tree": "clean before generated build artifacts",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "mmskeleton",
      "version": "0.7rc1+b4c076b",
      "import_names": ["mmskeleton"]
    }
  ],
  "evidence": {
    "source_roots": ["mmskeleton"],
    "docs": ["README.md", "doc/GETTING_STARTED.md", "doc/START_RECOGNITION.md", "doc/CUSTOM_DATASET.md", "doc/SKELETON_DATA.md", "doc/START_POSE_ESTIMATION.md", "doc/CREATE_APPLICATION.md"],
    "examples": ["resource/data_example", "resource/category_annotation_example.json"],
    "tests": [],
    "configs": ["configs/recognition", "configs/pose_estimation", "configs/apis", "configs/utils", "configs/mmdet"],
    "scripts": ["tools/get_stgcn_models.sh", "tools/stgcn_models.txt", "tools/publish_model.py", "tools/mmskl"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as
  potentially stale and refresh it.
- If the current checkout is dirty in source/docs/config paths, or the dirty
  paths differ from this baseline, refresh it.
- If `setup.py`, requirements, public processors, graph/model APIs, config
  entry points, or the documented MMDetection/HRNet integration changes,
  refresh the relevant sub-skill and verification artifacts.
- The generated runtime graph deliberately excludes generated build files,
  checkpoints, and review artifacts; changes only in those areas do not by
  themselves change the public evidence baseline.
