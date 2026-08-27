# Repository Provenance

## Purpose

This snapshot tells future agents whether the generated skill still matches the
repository checkout that was used to build it.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T17:45:45Z",
  "repository": {
    "name": "TabPFN",
    "remote_url": "https://github.com/PriorLabs/TabPFN.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "9262fa277b0fd92967f443e0f4171c3b2e745df7",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "tabpfn",
      "version": "8.3.0",
      "import_names": ["tabpfn"]
    }
  ],
  "evidence": {
    "source_roots": ["src/tabpfn/"],
    "docs": ["README.md"],
    "examples": ["examples/"],
    "scripts": ["scripts/"],
    "tests": ["tests/"],
    "configs": ["pyproject.toml"]
  }
}
```

## Refresh rule

Refresh the skill if the commit changes, the dirty paths change materially, or
package-level APIs, checkpoints, or docs no longer match this snapshot.
