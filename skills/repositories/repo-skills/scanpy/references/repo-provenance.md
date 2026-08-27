# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-skill-from-repo`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T00:00:00Z",
  "repository": {
    "name": "scanpy",
    "remote_url": "https://github.com/scverse/scanpy.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "39f12414fea9cea9439a3d9f665d1e17636092a9",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "scanpy",
      "version": "0.1.0.dev1+g39f12414f",
      "import_names": ["scanpy"]
    }
  ],
  "evidence": {
    "source_roots": [
      "src/scanpy"
    ],
    "docs": [
      "README.md",
      "docs/installation.md",
      "docs/basic_usage.md",
      "docs/api",
      "docs/tutorials",
      "docs/how-to",
      "docs/external"
    ],
    "examples": [
      "docs/tutorials",
      "docs/how-to"
    ],
    "tests": [
      "tests/test_readwrite.py",
      "tests/test_read_10x.py",
      "tests/test_preprocessing.py",
      "tests/test_qc_metrics.py",
      "tests/test_highly_variable_genes.py",
      "tests/test_pca.py",
      "tests/test_neighbors.py",
      "tests/test_clustering.py",
      "tests/test_embedding.py",
      "tests/test_paga.py",
      "tests/test_rank_genes_groups.py",
      "tests/test_plotting.py",
      "tests/test_plotting_embedded",
      "tests/external"
    ],
    "configs": [
      "pyproject.toml"
    ],
    "existing_skill_evidence": [
      "skills/scanpy"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-skill-from-repo`.
- If the current working tree dirty paths differ from this snapshot, review whether the changed files affect public APIs, docs, examples, tests, packaging, or optional dependencies.
- If package metadata, Python version support, optional extras, console entry points, or public API signatures changed even on the same commit, run `refresh-skill-from-repo`.
