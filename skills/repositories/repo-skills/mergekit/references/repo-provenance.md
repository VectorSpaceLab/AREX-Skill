# Repository Provenance

## Purpose

Read this before deciding whether the runtime skill matches a mergekit checkout.
If the commit, dirty state, package metadata, public entry points, or major
evidence paths differ, run a repo-skill refresh.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-23T09:11:27Z",
  "repository": {
    "name": "mergekit",
    "remote_url": "https://github.com/arcee-ai/mergekit.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "a6e402884ba9bc30da7f23e8304a35f19485de95",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "mergekit",
      "version": "0.1.4",
      "import_names": ["mergekit"]
    }
  ],
  "evidence": {
    "source_roots": ["mergekit/", "mergekit/_data/"],
    "docs": ["README.md", "docs/", "CONTRIBUTING.md"],
    "examples": ["examples/"],
    "tests": ["tests/"],
    "configs": ["pyproject.toml", "examples/", "mergekit/_data/architectures/", "mergekit/_data/chat_templates/"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, refresh the skill.
- This snapshot is intentionally dirty because generated runtime and review
  files are under `skills/`; compare only package-source changes when assessing
  staleness.
- If `pyproject.toml` changes its dependency ranges or console entry points,
  refresh even when the source commit is unchanged.
- If architecture definitions, tokenizer builders, CLI scripts, merge methods,
  or public docs change, refresh the nearest route and then reconcile the root.
