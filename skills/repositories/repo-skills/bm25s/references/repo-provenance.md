# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of
`bm25s`. If the current commit, dirty state, package metadata, or major
public evidence paths differ from this snapshot, run a repo-skill refresh.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-23T07:03:52Z",
  "repository": {
    "name": "bm25s",
    "remote_url": "https://github.com/xhluca/bm25s",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "ce881e16259d2bef5a8bf4a25156f8a4f60e8154",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "bm25s",
      "version": "0.0.0",
      "import_names": ["bm25s"]
    }
  ],
  "evidence": {
    "source_roots": ["bm25s"],
    "docs": ["README.md", "bm25s/high_level/README.md", "tests/README.md"],
    "examples": ["examples"],
    "tests": ["tests/core", "tests/high_level", "tests/numba", "tests/stopwords", "tests/data", "tests/comparison"],
    "configs": ["setup.py", "tests/requirements-core.txt", "tests/requirements-comparison.txt"]
  }
}
```

The `0.0.0` value is the setup fallback observed in this shallow untagged
checkout; it is not a release claim. Prefer the installed/released package
version when working from a published distribution.

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as
  potentially stale and refresh it.
- If the current working tree is dirty while this snapshot is clean, or the
  changed paths differ from a deliberately updated snapshot, refresh it.
- Refresh when `setup.py`, public modules, console entry points, supported
  extras, on-disk filenames, or the high-level/CLI/MCP/Hugging Face surfaces
  change even if the commit is otherwise known.
