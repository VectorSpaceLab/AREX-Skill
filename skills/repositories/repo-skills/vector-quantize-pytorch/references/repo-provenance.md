# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of `vector-quantize-pytorch`. If the current repo commit, package version, public API surface, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on this skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T13:33:42Z",
  "repository": {
    "name": "vector-quantize-pytorch",
    "remote_url": "https://github.com/lucidrains/vector-quantize-pytorch.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "19868fd03213a6762834a35069c8beda88b36f21",
    "working_tree": "clean at source-analysis time before generated skill artifacts were written",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "vector-quantize-pytorch",
      "version": "1.31.1",
      "import_names": ["vector_quantize_pytorch"]
    }
  ],
  "evidence": {
    "source_roots": ["vector_quantize_pytorch"],
    "docs": ["README.md"],
    "examples": ["examples"],
    "tests": ["tests"],
    "metadata": ["pyproject.toml"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, public exports in `vector_quantize_pytorch/__init__.py`, constructor signatures, or README workflow sections changed, refresh even if the commit looks close.
- If a downstream task depends on optional examples or dev-only integrations not verified by this skill, verify those paths separately or extend the skill.
