# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of
Gaussian-SLAM. If the commit, dirty source state, dependency pins, entry points,
or major evidence paths differ, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T00:00:00Z",
  "repository": {
    "name": "Gaussian-SLAM",
    "remote_url": "https://github.com/VladimirYugay/Gaussian-SLAM.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "eaec10d73ce7511563882b8856896e06d1f804e3",
    "working_tree": "dirty-production-artifacts-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["src", "gaussian_rasterizer", "simple_knn"]
    }
  ],
  "evidence": {
    "source_roots": ["src/entities", "src/evaluation", "src/utils"],
    "docs": ["README.md"],
    "entry_points": ["run_slam.py", "run_evaluation.py"],
    "configs": ["configs/Replica", "configs/TUM_RGBD", "configs/ScanNet", "configs/scannetpp"],
    "scripts": ["scripts/download_replica.sh", "scripts/download_tum.sh", "scripts/reproduce_sbatch.sh"],
    "dependencies": ["environment.yml"],
    "tests": []
  }
}
```

The source checkout had no package metadata, release version, or native test
suite. The only dirty path was the untracked `skills/` production area created
outside the source/runtime modules; no source file was reported modified.

## Refresh check

- Refresh if `git rev-parse HEAD` differs from the recorded commit.
- Refresh if source, configs, entry points, README, or `environment.yml` have
  uncommitted changes beyond the production-artifact state above.
- Refresh if either pinned CUDA-extension commit, PyTorch/CUDA combination,
  accepted dataset alias, checkpoint schema, or evaluator stage changes.
