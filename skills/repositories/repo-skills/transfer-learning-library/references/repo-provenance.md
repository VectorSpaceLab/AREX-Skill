# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Transfer Learning Library. If the current repo commit, dirty state, package version, dependencies, public APIs, docs, or examples differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T21:45:00Z",
  "repository": {
    "name": "Transfer-Learning-Library",
    "remote_url": "https://github.com/thuml/Transfer-Learning-Library.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "c4aa59eb565650a552b809411601d0589efbbfe4",
    "working_tree": "dirty-generated-skill-artifacts",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "tllib",
      "version": "0.4",
      "import_names": ["tllib"]
    }
  ],
  "evidence": {
    "source_roots": ["tllib"],
    "docs": ["README.md", "DATASETS.md", "docs/index.rst", "docs/tllib"],
    "examples": [
      "examples/domain_adaptation",
      "examples/domain_generalization",
      "examples/task_adaptation",
      "examples/semi_supervised_learning",
      "examples/model_selection"
    ],
    "tests": [],
    "configs": ["setup.py", "requirements.txt", "examples/**/requirements.txt"]
  }
}
```

## Evidence notes

- Source evidence was the public package source under `tllib/`, Sphinx API docs under `docs/tllib/`, top-level README/dataset notices, and workflow examples under `examples/`.
- No repo-owned `tests/` directory was present. Generated validation therefore uses public API smoke checks and native example/doc evidence rather than repo test execution.
- The dirty state recorded above is from generated `skills/` output. If a checkout has source, docs, setup metadata, or examples modified outside generated skill artifacts, treat this skill as potentially stale.
- TLLib 0.4 was verified against a compatibility stack from its original era: Python 3.8, PyTorch 1.8.1 CPU, TorchVision 0.9.1 CPU, and NumPy 1.23.5. Modern PyTorch/TorchVision/NumPy stacks may need the troubleshooting guidance in this skill.

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, run `refresh-repo-skill`.
- If `setup.py`, `requirements.txt`, `tllib/`, `docs/tllib/`, `README.md`, `DATASETS.md`, or `examples/` changed, run `refresh-repo-skill`.
- If the package version, import names, optional dependencies, dataset conventions, or public example workflows changed, run `refresh-repo-skill` even on the same commit.
