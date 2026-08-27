# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of DGL-LifeSci. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "evidence": {
    "configs": [
      "examples/property_prediction/csv_data_configuration/model_configures"
    ],
    "docs": [
      "README.md",
      "docs/source"
    ],
    "examples": [
      "examples"
    ],
    "package_metadata": [
      "python/setup.py",
      "python/dgllife/libinfo.py"
    ],
    "scripts": [
      "examples/property_prediction",
      "examples/reaction_prediction/rexgen_direct",
      "examples/binding_affinity_prediction",
      "examples/generative_models",
      "examples/molecule_embeddings",
      "examples/link_prediction"
    ],
    "source_roots": [
      "python/dgllife"
    ],
    "tests": [
      "tests/data",
      "tests/model",
      "tests/utils"
    ]
  },
  "generated_at_utc": "2026-06-29T00:00:00Z",
  "packages": [
    {
      "import_names": [
        "dgllife"
      ],
      "name": "dgllife",
      "version": "0.3.1"
    }
  ],
  "repository": {
    "branch": "master",
    "commit": "be8bc71d29ecf34a9dab7c7bd47c08f3383d9be0",
    "dirty_paths": [
      "skills/"
    ],
    "name": "dgl-lifesci",
    "remote_url": "https://github.com/awslabs/dgl-lifesci.git",
    "tag": null,
    "vcs": "git",
    "working_tree": "dirty"
  },
  "schema": "disco.repo-provenance.v1"
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths differ from `repository.dirty_paths`, treat the skill as potentially stale.
- If `python/dgllife`, public examples, docs, model constructors, dataset classes, or dependency requirements change, refresh the skill even on the same commit.
- Review the evidence paths above when deciding whether new DGL-LifeSci workflows need an extension rather than a refresh.
