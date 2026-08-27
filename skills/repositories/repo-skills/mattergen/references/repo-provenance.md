# Repository Provenance

Read this before deciding whether the MatterGen skill matches a checkout or
package installation. If the source commit, package entry points, or major
evidence paths differ, use the repository-skill refresh workflow.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T10:30:00Z",
  "repository": {
    "name": "mattergen",
    "remote_url": "https://github.com/microsoft/mattergen",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "ac9ddd406171138c3f037d06b9b53fedbbb1c536",
    "working_tree": "source-clean-at-generation; generated skill and review artifacts added afterward",
    "dirty_paths": ["skills/disco/mattergen", "skills/tests/mattergen"]
  },
  "packages": [
    {
      "name": "mattergen",
      "version": "1.0.3",
      "import_names": ["mattergen"]
    }
  ],
  "evidence": {
    "source_roots": ["mattergen"],
    "docs": ["README.md", "MODEL_CARD.md", "data-release/*/README.md"],
    "examples": ["README.md command recipes", "sampling_conf"],
    "tests": ["mattergen/tests", "mattergen/common/tests", "mattergen/diffusion/tests"],
    "configs": ["mattergen/conf", "sampling_conf", "checkpoints/*/config.yaml"]
  },
  "entry_points": [
    "mattergen-generate",
    "mattergen-train",
    "mattergen-finetune",
    "mattergen-evaluate",
    "csv-to-dataset"
  ]
}
```

## Refresh check

- Compare the current source commit with `ac9ddd406171138c3f037d06b9b53fedbbb1c536`.
- Check whether the five entry points, checkpoint catalog, config groups, and
  public generation/evaluation APIs still exist.
- Treat a change in torch/CUDA/PyG compatibility, property registry, CSV cache
  schema, evaluation correction schemes, or Hydra config layout as a reason to
  refresh and rerun verification.
- The `skills/disco/mattergen` and `skills/tests/mattergen` paths are generated
  outputs, not source evidence; do not interpret their presence as a source-code
  change when assessing package staleness.
