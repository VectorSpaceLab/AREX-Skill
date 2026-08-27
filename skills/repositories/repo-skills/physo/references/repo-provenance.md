# Repository Provenance

## Purpose

Use this snapshot to decide whether the skill matches a current PhySO checkout.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T00:00:00Z",
  "repository": {
    "name": "PhySO",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "bfbfa88d5def09d3d0cd47f3e2252b5a25836721",
    "working_tree": "dirty-generated-skill-artifacts-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "physo",
      "version": "1.2.0",
      "import_names": ["physo"]
    }
  ],
  "evidence": {
    "source_roots": ["physo"],
    "docs": ["README.md", "docs/source"],
    "examples": ["demos"],
    "tests": [
      "physo/task/tests",
      "physo/physym/tests",
      "physo/toolkit/tests",
      "physo/benchmark/FeynmanDataset/tests",
      "physo/benchmark/ClassDataset/tests"
    ],
    "scripts": [
      "demos/sr_quick_start.py",
      "demos/class_sr_quick_start.py",
      "benchmarking/FeynmanBenchmark/feynman_run.py",
      "benchmarking/ClassBenchmark/classbench_run.py"
    ],
    "package_files": ["setup.py", "pyproject.toml", "requirements.txt"],
    "review_artifacts": ["skills/tests/physo/reports/integration"]
  }
}
```

## Refresh Check

- Refresh if the commit or package version differs, or if source/docs/tests outside `skills/` change.
- If the generated skill is reused in another checkout with different public APIs, treat it as stale until refreshed.
