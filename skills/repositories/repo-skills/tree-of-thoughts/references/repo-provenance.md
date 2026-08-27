# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state outside generated skill/artifact paths, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T20:12:56Z",
  "repository": {
    "name": "tree-of-thoughts",
    "remote_url": "https://github.com/kyegomez/tree-of-thoughts.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "b6197795423c9d0ac3b84d0019f8cd82b201f600",
    "working_tree": "dirty-generated-artifacts",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "tree-of-thoughts",
      "version": "0.6.5",
      "import_names": ["tree_of_thoughts"]
    }
  ],
  "evidence": {
    "source_roots": ["tree_of_thoughts/"],
    "docs": ["README.md", "prompts.txt"],
    "examples": ["example.py", "examples/dfs.py", "examples/bfs.py"],
    "tests": [],
    "configs": ["pyproject.toml", "requirements.txt"],
    "scripts": ["scripts/"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If source files under `tree_of_thoughts/`, package metadata, examples, or prompt docs changed, run `refresh-repo-skill`.
- Ignore differences caused solely by regenerated skill artifacts under `skills/` when comparing dirty paths.
- If public entry points change, especially root exports or the BFS import location, run `refresh-repo-skill`.
