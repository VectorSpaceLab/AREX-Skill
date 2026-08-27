# Repository Provenance

This snapshot records the checkout state used to build the generated repo skill. If the current commit, dirty state, package facts, or major evidence paths differ, refresh the skill.

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T21:18:28Z",
  "repository": {
    "name": "contrastive-unpaired-translation",
    "remote_url": "https://github.com/taesungp/contrastive-unpaired-translation.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "b3ac297708dfb6f7589d04662277e53c0d579c27",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/contrastive-unpaired-translation.log",
      "skills/disco/contrastive-unpaired-translation/ (generated repo skill files)",
      "skills/tests/contrastive-unpaired-translation/ (integration artifacts)"
    ]
  },
  "packages": [
    {
      "name": "contrastive-unpaired-translation",
      "version": null,
      "import_names": ["train", "test", "options", "data", "models", "util", "experiments"]
    }
  ],
  "evidence": {
    "source_roots": ["data", "models", "options", "util", "experiments", "datasets"],
    "docs": ["README.md", "docs/datasets.md"],
    "examples": ["datasets/single_image_monet_etretat"],
    "tests": [],
    "configs": ["environment.yml", "requirements.txt", "tox.ini"]
  }
}
```

## Notes

- The checkout already contained an untracked `skills/contrastive-unpaired-translation.log` file before the generated skill was written.
- The generated skill content itself lives under `skills/disco/contrastive-unpaired-translation/` and is not treated as part of the source baseline.
- No installable Python distribution metadata was present in the repository, so the package name is recorded as the checkout name with a null version.
