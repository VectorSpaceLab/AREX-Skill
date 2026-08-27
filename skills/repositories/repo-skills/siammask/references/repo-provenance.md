# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of SiamMask. If the current repo commit, dirty state, package/import layout, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T18:35:44Z",
  "repository": {
    "name": "SiamMask",
    "remote_url": "https://github.com/foolwood/SiamMask.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "a2b3ce3dca23b3a911d96b791e007eec6d39a625",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "SiamMask-source-tree",
      "version": null,
      "import_names": ["models", "datasets", "tools", "utils"]
    }
  ],
  "evidence": {
    "source_roots": ["models", "datasets", "utils", "tools"],
    "docs": ["README.md", "data/coco/readme.md", "data/det/readme.md", "data/vid/readme.md", "data/ytb_vos/readme.md"],
    "examples": ["data/tennis", "experiments/siammask_base", "experiments/siammask_sharp", "experiments/siamrpn_resnet"],
    "tests": [],
    "configs": [
      "experiments/siammask_base/config.json",
      "experiments/siammask_sharp/config.json",
      "experiments/siammask_sharp/config_davis.json",
      "experiments/siammask_sharp/config_vot.json",
      "experiments/siammask_sharp/config_vot18.json",
      "experiments/siamrpn_resnet/config.json"
    ],
    "scripts": ["make.sh", "tools", "data"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If source files under `models/`, `datasets/`, `utils/`, `tools/`, `experiments/`, `data/`, or `requirements.txt` changed, refresh the skill even if the commit did not change.
- This repo has no packaging metadata; changes to checkout-style import roots or required `PYTHONPATH` behavior are skill-relevant.
- Generated skill output under `skills/` is not source evidence for staleness unless the user is refreshing this skill itself.
