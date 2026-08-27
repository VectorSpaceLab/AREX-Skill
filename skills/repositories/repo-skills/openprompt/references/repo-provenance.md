# Repository Provenance

## Purpose

Read this before deciding whether the skill is current for a checkout of OpenPrompt. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T20:07:06Z",
  "repository": {
    "name": "OpenPrompt",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "f6fb080ef755c37c01b7959e7560d007049510e8",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "openprompt",
      "version": "1.0.1",
      "import_names": ["openprompt"]
    }
  ],
  "evidence": {
    "source_roots": ["openprompt/"],
    "docs": ["README.md", "docs/source/"],
    "examples": ["tutorial/", "experiments/"],
    "tests": ["test/test_data_processor/"],
    "configs": ["experiments/", "requirements.txt", "setup.py"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the commit above, treat the skill as stale.
- If the checkout gains or loses generated skill files or the dirty-path shape changes materially, refresh the skill.
- If package metadata or public entry points change even on the same commit, refresh the skill.
