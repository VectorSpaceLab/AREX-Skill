# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T12:52:23Z",
  "repository": {
    "name": "stumpy",
    "remote_url": "https://github.com/stumpy-dev/stumpy.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "55f63a127276bde5be8b7ffb6565ff29b070c278",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "stumpy",
      "version": "1.14.1",
      "import_names": ["stumpy"]
    }
  ],
  "evidence": {
    "source_roots": ["stumpy/"],
    "docs": ["README.rst", "docs/api.rst", "docs/install.rst", "docs/tutorials.rst", "docs/Tutorial_*.ipynb"],
    "examples": ["README.rst code snippets", "stable tutorial notebooks under docs/"],
    "tests": ["tests/test_stump.py", "tests/test_aamp.py", "tests/test_mstump.py", "tests/test_motifs.py", "tests/test_mpdist.py", "tests/test_floss.py", "tests/test_scrump.py", "tests/test_stumpi.py", "tests/test_stimp.py", "tests/test_stumped.py", "tests/test_gpu_*.py", "tests/test_ray.py"],
    "configs": ["pyproject.toml", "requirements.txt", "environment.yml", "pytest.ini", "conftest.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or if dirty paths differ materially from `skills/` generation artifacts, run `refresh-repo-skill`.
- If `pyproject.toml`, public API exports, optional dependency behavior, docs tutorials, or representative tests change, run `refresh-repo-skill`.
- If the target task requires a backend that was optional-unverified here (CUDA or Ray), verify that backend in the target runtime before relying on its workflow guidance.
