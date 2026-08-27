# Repository Provenance

## Purpose

Read this before deciding whether this Aim skill is current for a checkout. If the current repo commit, dirty state, package metadata, entry points, or evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T06:05:43Z",
  "repository": {
    "name": "aim",
    "remote_url": "https://github.com/aimhubio/aim.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "6e098e38065364c76b2bb7c028f266e53b647642",
    "working_tree": "dirty-generated-skill-artifacts",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "aim",
      "version": "3.29.1",
      "import_names": ["aim"]
    },
    {
      "name": "aim-ui",
      "version": "3.29.1",
      "import_names": []
    },
    {
      "name": "aimrecords",
      "version": "0.0.7",
      "import_names": ["aimrecords"]
    },
    {
      "name": "aimrocks",
      "version": "0.5.2",
      "import_names": ["aimrocks"]
    }
  ],
  "evidence": {
    "source_roots": ["aim/"],
    "metadata": ["setup.py", "pyproject.toml", "requirements.txt", "aim/VERSION"],
    "docs": ["README.md", "docs/source/quick_start/", "docs/source/using/", "docs/source/refs/", "docs/source/understanding/"],
    "examples": ["examples/"],
    "tests": ["tests/sdk/", "tests/storage/", "tests/ext/", "tests/api/"],
    "troubleshooting": ["troubleshooting/TROUBLESHOOTING.md"],
    "existing_skill_artifacts": ["skills/aim.log"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has source, docs, examples, tests, metadata, or CLI changes not represented here, refresh the skill.
- If public entry points (`aim`, `aim-watcher`), `setup.py` dependencies, `Run`/`Repo` signatures, adapter names, or CLI help output changed, refresh the skill even if the commit looks close.
- Ignore changes confined to generated skill output or review artifacts unless refreshing this skill itself.
