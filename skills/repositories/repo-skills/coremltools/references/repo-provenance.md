# Repository Provenance

## Purpose

Read this before deciding whether the `coremltools` repo skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T08:19:04Z",
  "repository": {
    "name": "coremltools",
    "remote_url": "https://github.com/apple/coremltools.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "375ce908fa5a6381e9ad003dda026183f6c3bebf",
    "commit_date": "2026-08-10T17:36:40-07:00",
    "commit_subject": "Do not add MIL's stability epsilon in torch.reciprocal (#2773)",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "coremltools",
      "version": "9.1.dev1",
      "import_names": ["coremltools"]
    }
  ],
  "evidence": {
    "source_roots": ["coremltools/"],
    "docs": ["README.md", "BUILDING.md", "docs/", "docs-guides/source/", "mlmodel/docs/"],
    "examples": ["examples/README.md", "docs-guides/source/*.md"],
    "tests": ["coremltools/test/"],
    "requirements": ["setup.py", "reqs/*.pip"],
    "scripts": ["scripts/"],
    "reference_only": ["coremlpython/", "milstoragepython/", "modelpackage/src/", "coremltools/modelrunner/", "mlmodel/format/"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the snapshot commit, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package version, public converter signatures, `MLModel` signatures, or optimize config APIs changed, refresh even on the same commit.
- If the current checkout has uncommitted source changes outside generated skill artifacts, refresh before relying on this skill.
- If future work requires verified macOS prediction, ModelRunner, TensorFlow, or optional framework coverage that was not part of this construction, extend or refresh the skill with the corresponding environment evidence.
