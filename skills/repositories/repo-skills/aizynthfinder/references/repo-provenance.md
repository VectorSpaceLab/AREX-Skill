# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of AiZynthFinder. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-23T00:00:00Z",
  "repository": {
    "name": "aizynthfinder",
    "remote_url": "https://github.com/MolecularAI/aizynthfinder",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "21ff546d5f22331b078390a2f12dc04defc3f39c",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "aizynthfinder",
      "version": "4.4.1",
      "import_names": ["aizynthfinder"]
    }
  ],
  "evidence": {
    "source_roots": ["aizynthfinder"],
    "docs": ["README.md", "docs"],
    "examples": ["contrib/notebook.ipynb", "plugins"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "env-dev.yml", "aizynthfinder/data"],
    "scripts": ["aizynthfinder/interfaces", "aizynthfinder/tools", "tasks.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has source, docs, config, tests, or package metadata changes outside the generated `skills/` tree, run `refresh-repo-skill`.
- If package metadata, console entry points, public APIs, optional extras, config schema, search algorithms, or output formats changed even on the same commit, run `refresh-repo-skill`.
- If user tasks depend on optional plugins or services that have changed independently, refresh or extend the relevant sub-skill before relying on old guidance.
