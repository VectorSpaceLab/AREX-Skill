# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a PaddleHelix checkout. If the current commit, dirty state, package metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on detailed guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-29T00:00:00Z",
  "repository": {
    "name": "PaddleHelix",
    "remote_url": "https://github.com/PaddlePaddle/PaddleHelix.git",
    "vcs": "git",
    "branch": "dev",
    "tag": null,
    "commit": "8e3991ab1209134b148b05d44e784a43eaa4484d",
    "working_tree": "dirty",
    "dirty_paths": [
      "paddlehelix.egg-info/",
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "paddlehelix",
      "version": "1.0.0b",
      "import_names": ["pahelix"]
    }
  ],
  "evidence": {
    "source_roots": [
      "pahelix/",
      "c/pahelix/toolkit/linear_rna/"
    ],
    "docs": [
      "README.md",
      "installation_guide.md",
      "developer_guide.md",
      "docs/",
      "tutorials/"
    ],
    "examples": [
      "apps/pretrained_compound/",
      "apps/molecular_generation/",
      "apps/drug_target_interaction/",
      "apps/drug_drug_synergy/",
      "apps/fewshot_molecular_property/",
      "apps/molecular_docking/helixdock/",
      "apps/pretrained_protein/",
      "apps/protein_function_prediction/",
      "apps/protein_protein_interaction/",
      "apps/helixprotx/",
      "apps/protein_folding/"
    ],
    "tests": [
      "pahelix/tests/",
      "pahelix/utils/tests/"
    ],
    "configs": [
      "setup.py",
      "apps/**/requirements*.txt",
      "apps/**/configs/",
      "apps/protein_folding/**/data_configs/",
      "apps/protein_folding/**/train_configs/"
    ],
    "excluded_or_reference_only": [
      "competition/",
      "research/",
      "apps/protein_folding/**/scripts/download_*.sh"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If the current working tree is clean but this snapshot is dirty, or dirty paths differ materially from the listed paths, refresh before publication or import.
- If `setup.py`, `pahelix/`, `apps/`, `c/pahelix/toolkit/linear_rna/`, `docs/`, or `tutorials/` changed, refresh the affected sub-skills.
- If PaddleHelix changes dependency names, app launchers, HelixFold schemas, LinearRNA bindings, or package version metadata, refresh before using generated commands or validators.
