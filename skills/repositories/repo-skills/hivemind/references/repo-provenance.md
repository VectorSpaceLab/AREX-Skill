# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the commit, dirty state, package version, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T21:47:38Z",
  "repository": {
    "name": "hivemind",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "4bd43b77895019b20d18d81d0d0c1a5ab9a10847",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "hivemind",
      "version": "1.2.0.dev0",
      "import_names": ["hivemind"]
    }
  ],
  "evidence": {
    "source_roots": [
      "hivemind",
      "hivemind/dht",
      "hivemind/averaging",
      "hivemind/compression",
      "hivemind/moe",
      "hivemind/optim",
      "hivemind/hivemind_cli"
    ],
    "docs": ["README.md", "docs", "docs/modules", "docs/user"],
    "examples": ["examples/albert"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "setup.py", "requirements.txt", "requirements-dev.txt", "requirements-docs.txt", "examples/albert/requirements.txt", "hivemind/hivemind_cli/config.yml"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` changes, treat this skill as potentially stale.
- If the working tree becomes dirty or the dirty paths differ from this snapshot, refresh the skill.
- If the installed `hivemind` version or public entry points change, refresh the skill.
