# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-skill-from-repo`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T00:00:00Z",
  "repository": {
    "name": "segment-anything",
    "remote_url": "https://github.com/facebookresearch/segment-anything.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "dca509fe793f601edb92606367a655c15ac00fdf",
    "working_tree": "clean-before-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "segment_anything",
      "version": "1.0",
      "import_names": ["segment_anything"]
    }
  ],
  "evidence": {
    "source_roots": ["segment_anything"],
    "docs": ["README.md", "demo/README.md"],
    "examples": ["notebooks/predictor_example.ipynb", "notebooks/automatic_mask_generator_example.ipynb", "notebooks/onnx_model_example.ipynb", "demo/src"],
    "scripts": ["scripts/amg.py", "scripts/export_onnx_model.py"],
    "tests": [],
    "configs": ["setup.py", "setup.cfg", "demo/configs"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-skill-from-repo`.
- If the current working tree has source, docs, examples, scripts, package metadata, or demo changes not represented in this snapshot, run `refresh-skill-from-repo`.
- If package metadata, public API signatures, model registry keys, script flags, or optional dependency behavior changed even on the same commit, refresh the skill.
