# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the commit, dirty state, package version, public entry points, or
major evidence paths differ, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T18:47:42Z",
  "repository": {
    "name": "skrl",
    "remote_url": "https://github.com/Toni-SM/skrl",
    "vcs": "git",
    "branch": "develop",
    "tag": "2.1.0",
    "commit": "3cdc7f3bacc1fd487249a296d6107da64a990c48",
    "working_tree": "dirty: generated skill and review artifacts under skills/",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "skrl",
      "version": "2.1.0",
      "import_names": ["skrl"]
    }
  ],
  "evidence": {
    "source_roots": ["skrl"],
    "docs": ["README.md", "docs/source/intro", "docs/source/api", "docs/source/snippets"],
    "examples": ["examples/gym", "examples/gymnasium", "examples/shimmy", "examples/isaaclab", "examples/mani_skill", "examples/playground"],
    "tests": ["tests/agents", "tests/envs", "tests/memories", "tests/multi_agents", "tests/trainers", "tests/utils", "tests/test_torch_config.py", "tests/test_jax_config.py", "tests/test_warp_config.py"],
    "configs": ["pyproject.toml"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat this graph as
  potentially stale and run `refresh-repo-skill`.
- If the current dirty paths differ materially from this snapshot, refresh
  before relying on source-specific details.
- If package metadata, public entry points, framework extras, wrapper tags,
  Runner component mappings, or model role contracts changed, refresh even when
  the commit appears unchanged.
