# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of SaProt. If the current commit, dirty state, package layout, public APIs, scripts, configs, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-29T00:00:00Z",
  "repository": {
    "name": "SaProt",
    "remote_url": "https://github.com/westlake-repl/SaProt.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "e91e4858b55944523f1f8d385f7b96a0d3d34c1d",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "source-checkout-no-distribution-metadata",
      "version": null,
      "import_names": [
        "model",
        "dataset",
        "utils"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "model/",
      "dataset/",
      "utils/"
    ],
    "docs": [
      "README.md",
      "model/README.md",
      "dataset/README.md",
      "LMDB/README.md",
      "bin/README.md",
      "weights/PLMs/README.md"
    ],
    "examples": [
      "example/8ac8.cif"
    ],
    "configs": [
      "config/"
    ],
    "scripts": [
      "scripts/training.py",
      "scripts/mutation_zeroshot.py",
      "scripts/compute_clinvar_auc.py",
      "environment.sh"
    ],
    "tests": []
  },
  "inspection": {
    "python_environment": "private-inspection-environment-redacted",
    "verified_imports": [
      "utils.foldseek_util",
      "dataset.data_interface",
      "model.model_interface"
    ],
    "heavy_dependencies_not_installed_for_inspection": [
      "torch",
      "transformers",
      "pytorch_lightning",
      "torchmetrics"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and refresh it.
- If dirty paths differ from the snapshot, refresh when those paths affect public docs, configs, source modules, examples, scripts, or generated skill content.
- If SaProt adds packaging metadata, changes model/dataset class names, changes task YAML structure, changes Foldseek conversion behavior, or updates dependency pins, refresh this skill.
- If model checkpoint naming, AA-only caveats, or benchmark workflows change in the public README, refresh this skill even if source modules are unchanged.
