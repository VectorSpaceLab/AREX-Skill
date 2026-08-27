# Repository Provenance

## Purpose

Read this before deciding whether this Mesa skill is current for a checkout. If the current repo commit, dirty state, package version, public APIs, examples, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T17:43:52Z",
  "repository": {
    "name": "Mesa",
    "remote_url": "https://github.com/mesa/mesa.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "66f405f576e2bc6a7b8d48c6f686e9c444dba98b",
    "working_tree": "clean-before-generated-skill-output",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "Mesa",
      "version": "4.0.0a0",
      "import_names": ["mesa"]
    }
  ],
  "evidence": {
    "source_roots": [
      "mesa",
      "mesa/discrete_space",
      "mesa/experimental",
      "mesa/time",
      "mesa/visualization"
    ],
    "docs": [
      "README.md",
      "docs/overview.md",
      "docs/getting_started.md",
      "docs/apis",
      "docs/tutorials",
      "docs/best-practices.md",
      "docs/migration_guide.md"
    ],
    "examples": [
      "mesa/examples/basic",
      "mesa/examples/advanced",
      "mesa/examples/experimental"
    ],
    "tests": [
      "tests/test_agent.py",
      "tests/test_agentset.py",
      "tests/test_model.py",
      "tests/test_datacollector.py",
      "tests/time",
      "tests/discrete_space",
      "tests/experimental",
      "tests/visualization",
      "tests/examples"
    ],
    "configs": ["pyproject.toml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the source checkout has non-generated modifications to files in the evidence paths above, refresh before relying on fine API details.
- If package metadata, optional extras, public signatures, example names, visualization components, or experimental API status changed even on the same commit, refresh.
- This snapshot intentionally excludes generated skill output and review artifacts from the source dirty-state baseline.
