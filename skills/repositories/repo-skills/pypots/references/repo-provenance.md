# Repository Provenance

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T16:02:48Z",
  "repository": {
    "name": "PyPOTS",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "53b3eac34be9491ac3f28e65ee1993436e9318af",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "pypots",
      "version": "1.5",
      "import_names": ["pypots"]
    }
  ],
  "evidence": {
    "source_roots": ["pypots/"],
    "docs": ["README.md", "docs/"],
    "examples": ["examples/"],
    "tests": ["tests/"],
    "configs": ["pyproject.toml", "requirements/"],
    "scripts": ["scripts/"]
  }
}
```

## Refresh Check

Treat this skill as stale if any of the following change:

- `git rev-parse HEAD` no longer matches the recorded commit.
- The working tree dirty paths differ in a meaningful way.
- `pypots.__version__` changes.
- Public task APIs, CLI commands, or package entry points change.

When that happens, run `refresh-repo-skill` instead of assuming the generated
routes are still correct.
