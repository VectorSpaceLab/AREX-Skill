# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of pyAudioAnalysis. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T06:01:14Z",
  "repository": {
    "name": "pyAudioAnalysis",
    "remote_url": "https://github.com/tyiannak/pyAudioAnalysis.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "3dd60a2e904d11465b7a27332d1f4ce69182fa93",
    "working_tree": "dirty-generated-skill-output-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "pyAudioAnalysis",
      "version": "0.3.14",
      "import_names": [
        "pyAudioAnalysis"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "pyAudioAnalysis/"
    ],
    "docs": [
      "README.md",
      "tests/README.md"
    ],
    "examples": [
      "pyAudioAnalysis/data/",
      "tests/cmd_test_*.sh",
      "tests/script_*.py"
    ],
    "tests": [
      "pytests/",
      "tests/"
    ],
    "configs": [
      "setup.py",
      "requirements.txt"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata changes (distribution name, version, dependencies, package data, or public command/API files), refresh the skill even on the same commit.
- If the legacy CLI parser in `audioAnalysis.py` changes, refresh `sub-skills/cli-and-io` and the command references.
- If dependencies move to a new Python compatibility range or optional media dependencies change, refresh root troubleshooting and environment checks.
- This provenance intentionally records only relative evidence paths and public package facts. It omits local environment prefixes, Python executables, cache paths, and package installation locations.
