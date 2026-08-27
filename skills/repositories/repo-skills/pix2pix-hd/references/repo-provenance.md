# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of pix2pixHD. If the current repo commit, dirty state, or evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T19:44:33Z",
  "repository": {
    "name": "pix2pixHD",
    "remote_url": "https://github.com/NVIDIA/pix2pixHD.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "14b3b3c7fff413086e3b58df52096f16b6891172",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "torch",
      "version": "2.13.0+cu130",
      "import_names": ["torch"]
    },
    {
      "name": "torchvision",
      "version": "0.28.0+cu130",
      "import_names": ["torchvision"]
    },
    {
      "name": "dominate",
      "version": "2.9.1",
      "import_names": ["dominate"]
    },
    {
      "name": "scikit-learn",
      "version": "1.9.0",
      "import_names": ["sklearn"]
    }
  ],
  "evidence": {
    "source_roots": ["data", "models", "options", "util"],
    "docs": ["README.md"],
    "examples": ["scripts/test_512p.sh", "scripts/train_512p.sh", "scripts/test_512p_feat.sh", "scripts/train_512p_feat.sh"],
    "tests": [],
    "configs": ["_config.yml"],
    "fixtures": ["datasets/cityscapes"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, run a refresh.
- If the dirty paths change materially, run a refresh.
- If the source roots, scripts, or helper workflows change, run a refresh.
