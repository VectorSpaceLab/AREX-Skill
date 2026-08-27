# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, or major
evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-19T14:02:09Z",
  "repository": {
    "name": "Attention-Gated-Networks",
    "remote_url": "https://github.com/ozan-oktay/Attention-Gated-Networks.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "eee4881fdc31920efd873773e0b744df8dacbfb6",
    "working_tree": "clean-before-generated-output",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "AttentionGatedNetworks",
      "version": "1.0",
      "import_names": ["models", "dataio", "utils"]
    }
  ],
  "evidence": {
    "source_roots": ["models", "dataio", "utils"],
    "docs": ["README.md"],
    "examples": [
      "train_classifaction.py",
      "test_classification.py",
      "train_segmentation.py",
      "validation.py",
      "visualise_attention.py",
      "visualise_att_maps_epoch.py",
      "visualise_fmaps.py"
    ],
    "tests": [],
    "configs": [
      "configs/config_sononet_8.json",
      "configs/config_sononet_grid_att_8.json",
      "configs/config_sononet_grid_att_8_deepsup.json",
      "configs/config_sononet_grid_att_8_ft.json",
      "configs/config_unet_ct_dsv.json",
      "configs/config_unet_ct_multi_att_dsv.json"
    ],
    "excluded": [
      "checkpoints",
      "figures",
      "AttentionGatedNetworks.egg-info",
      "__pycache__",
      "skills/tests"
    ]
  }
}
```

The source checkout was clean before the generated skill files and review
artifacts were written. Generated files under `skills/` are not source evidence
for this snapshot.

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If non-generated source paths are dirty and this snapshot was clean, run
  `refresh-repo-skill`.
- If package metadata, public model registry names, dataset layouts, config
  fields, or generated helper behavior changed even on the same commit, run
  `refresh-repo-skill`.
