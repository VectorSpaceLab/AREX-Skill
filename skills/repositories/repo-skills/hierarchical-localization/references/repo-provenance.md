# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Hierarchical-Localization. If the current repo commit, dirty state, package version, public APIs, CLI flags, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T12:42:23Z",
  "repository": {
    "name": "Hierarchical-Localization",
    "remote_url": "https://github.com/cvg/Hierarchical-Localization.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "c13273bd0ecc2917a35910fd843712a1c6243193",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "hloc",
      "version": "1.5",
      "import_names": ["hloc"]
    }
  ],
  "evidence": {
    "source_roots": ["hloc/"],
    "docs": ["README.md", "hloc/pipelines/*/README.md", "datasets/sacre_coeur/README.md"],
    "examples": ["demo.ipynb", "pipeline_Aachen.ipynb", "pipeline_InLoc.ipynb", "pipeline_SfM.ipynb", "pairs/"],
    "tests": [],
    "configs": ["setup.py", "requirements.txt", ".github/workflows/code-quality.yml"],
    "excluded": ["third_party/", "dataset downloads", "benchmark-scale pipeline runs", "review/test artifact outputs"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths differ from `dirty_paths`, check whether the differences touch package code, docs, examples, requirements, or pipeline entry points; refresh when they do.
- If `hloc.__version__`, `setup.py`, `requirements.txt`, public module signatures, CLI flags, or configuration names change, refresh even if the commit is the same.
- The `skills/` dirty state in this snapshot is generation/output-related; it is not public package source evidence.
