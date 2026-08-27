# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T13:22:33Z",
  "repository": {
    "name": "SuperGluePretrainedNetwork",
    "remote_url": "https://github.com/magicleap/SuperGluePretrainedNetwork.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "ddcf11f42e7e0732a0c4607648f9448ea8d73590",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["models"]
    }
  ],
  "evidence": {
    "source_roots": ["models/"],
    "docs": ["README.md", "LICENSE"],
    "examples": ["demo_superglue.py", "match_pairs.py", "assets/freiburg_sequence/", "assets/scannet_sample_images/", "assets/phototourism_sample_images/"],
    "tests": [],
    "configs": ["requirements.txt", "assets/*_pairs*.txt", "assets/megadepth_*_scenes.txt"],
    "weights": ["models/weights/superpoint_v1.pth", "models/weights/superglue_indoor.pth", "models/weights/superglue_outdoor.pth"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If a checkout has new or changed top-level scripts, model modules, pair-file schemas, or checkpoint naming, run `refresh-repo-skill`.
- If the repository becomes a packaged distribution or changes import roots, refresh setup and API guidance.
- The dirty path recorded here is the generated `skills/` production output; if future source paths under `models/`, top-level scripts, `README.md`, `requirements.txt`, or `assets/` are dirty, refresh before relying on this skill.
