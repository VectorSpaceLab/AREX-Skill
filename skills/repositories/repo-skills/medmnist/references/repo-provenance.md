# Repository provenance

Read this before deciding whether the operating skill still matches a
checkout. If the commit, package version, public entry points, or evidence
paths differ, use a repository-skill refresh.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T19:15:30Z",
  "repository": {
    "name": "MedMNIST",
    "remote_url": "https://github.com/MedMNIST/MedMNIST/",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "805b74237fb5bd2db376fd94e50646b6a8905d9d",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "medmnist",
      "version": "3.0.2",
      "import_names": ["medmnist"]
    }
  ],
  "evidence": {
    "source_roots": ["medmnist"],
    "docs": ["README.md", "on_medmnist_plus.md"],
    "examples": ["examples/dataset_without_pytorch.py", "examples/getting_started.ipynb", "examples/getting_started_without_PyTorch.ipynb"],
    "tests": [],
    "configs": ["setup.py", "requirements.txt"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as
  potentially stale.
- If the current checkout is dirty or changed paths differ from the snapshot,
  refresh before using source-specific claims.
- If `setup.py`, `requirements.txt`, `medmnist/info.py`, `medmnist/dataset.py`,
  `medmnist/evaluator.py`, `medmnist/utils.py`, `medmnist/__main__.py`, or the
  documented examples change materially, refresh even when the commit is
  unchanged in a copied skill.
- This skill intentionally excludes external experiment repositories, downloaded
  NPZ files, generated assets, and review artifacts from runtime evidence.
