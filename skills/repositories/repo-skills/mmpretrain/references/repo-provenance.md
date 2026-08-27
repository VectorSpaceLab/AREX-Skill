# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an MMPreTrain checkout or installed package. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T17:55:15Z",
  "repository": {
    "name": "mmpretrain",
    "remote_url": "https://github.com/open-mmlab/mmpretrain.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "ee7f2e88501f61aa95c742dd5f429f039935ee90",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "mmpretrain",
      "version": "1.2.0",
      "import_names": ["mmpretrain"]
    }
  ],
  "evidence": {
    "source_roots": ["mmpretrain/"],
    "docs": ["README.md", "docs/en/"],
    "examples": ["demo/"],
    "tests": ["tests/"],
    "configs": ["configs/", "mmpretrain/configs/"],
    "metadata": ["setup.py", "setup.cfg", "requirements/", "model-index.yml", "dataset-index.yml"],
    "tools": ["tools/", "projects/"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths differ in source, docs, configs, tests, or tools (not just generated skill artifacts), run `refresh-repo-skill`.
- If `mmpretrain.__version__`, public API signatures, MIM packaging behavior, config families, or tool commands changed, run `refresh-repo-skill` even if the commit is unchanged.
- If optional backend support changes (CUDA/MMCV/PyTorch compatibility, multimodal extras, TorchServe tools), re-run environment verification before trusting backend-specific guidance.
