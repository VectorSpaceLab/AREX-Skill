# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a PyTorch Geometric checkout. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-skill-from-repo`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T00:00:00Z",
  "repository": {
    "name": "pytorch_geometric",
    "remote_url": "https://github.com/pyg-team/pytorch_geometric.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "1f0661ce88272d03f654b6bb0a2a3cb76b3e6aff",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "torch-geometric",
      "version": "2.9.0",
      "import_names": ["torch_geometric"]
    },
    {
      "name": "torch",
      "version": "2.12.1+cpu",
      "import_names": ["torch"]
    }
  ],
  "evidence": {
    "source_roots": ["torch_geometric", "graphgym"],
    "docs": ["README.md", "docs/source/install", "docs/source/get_started", "docs/source/tutorial", "docs/source/advanced", "docs/source/modules", "docs/source/cheatsheet"],
    "examples": ["examples"],
    "tests": ["test"],
    "configs": ["graphgym/configs", "test/my_config.yaml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-skill-from-repo`.
- If the current working tree has non-skill source, docs, examples, tests, config, or dependency changes not represented above, refresh before relying on API or workflow details.
- If `torch-geometric` package metadata, public import names, optional extras, or major module layout changes, refresh even when the commit is unchanged.
