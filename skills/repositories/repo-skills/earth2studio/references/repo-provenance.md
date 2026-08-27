# Repository Provenance

Read this before deciding whether this operating graph is current for an
Earth2Studio checkout. If the commit, dirty state, package version, public
entry points, or major evidence paths differ, refresh the graph before relying
on detailed claims.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-22T03:30:00Z",
  "repository": {
    "name": "earth2studio",
    "remote_url": "https://github.com/NVIDIA/earth2studio",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "2e3d1fd9a3f38391f8b27606e1d202a7eae83f95",
    "working_tree": "dirty",
    "dirty_paths": ["skills/earth2studio.log", "skills/disco/", "skills/tests/"]
  },
  "packages": [{
    "name": "earth2studio",
    "version": "0.18.0a0",
    "import_names": ["earth2studio"]
  }],
  "evidence": {
    "source_roots": ["earth2studio", "earth2studio/data", "earth2studio/lexicon", "earth2studio/models", "earth2studio/io", "earth2studio/serve"],
    "docs": ["README.md", "docs/userguide", "docs/modules", "serve/README.md", "serve/client/README.md", "serve/server/README.md"],
    "examples": ["examples"],
    "tests": ["test/data", "test/io", "test/lexicon", "test/models", "test/perturbation", "test/run", "test/statistics", "test/serve"],
    "configs": ["pyproject.toml", "serve/server/conf", "serve/server/env.example"]
  }
}
```

The generated runtime skill and its review artifacts are in the dirty working
tree; they are not package source evidence.

## Refresh check

- Compare `git rev-parse HEAD` with the snapshot commit.
- Compare source dirty paths and package metadata; generated skill/artifact
  paths may be ignored when judging package staleness.
- Recheck public exports, optional extras/conflicts, model/data protocols,
  serving APIs, and evidence roots after source changes.
- Re-run backend-aware verification when model APIs, CUDA requirements,
  compiled extras, or serving dependencies change.
