# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Open
Interface. If the current repo commit, dirty state, package version, public
entry points, or major evidence paths differ from this snapshot, run
`refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T13:21:27Z",
  "repository": {
    "name": "Open-Interface",
    "remote_url": "https://github.com/AmberSahdev/Open-Interface.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "5a4f706223507fc9d9eb2239cced85385fcb1308",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/ (untracked production log, generated runtime skill, and review artifacts)"
    ]
  },
  "packages": [
    {
      "name": "Open Interface",
      "version": "0.9.0",
      "import_names": [
        "app",
        "core",
        "interpreter",
        "llm",
        "models",
        "ui",
        "utils"
      ],
      "distribution_metadata": null
    }
  ],
  "evidence": {
    "source_roots": [
      "app"
    ],
    "docs": [
      "README.md",
      "app/README.md",
      "MEDIA.md"
    ],
    "examples": [],
    "tests": [
      "tests/simple_test.py"
    ],
    "configs": [
      "requirements.txt",
      ".python-version",
      ".github/workflows/pylint.yml"
    ],
    "scripts": [
      "build.py",
      "assets/mov_to_2x_mov_and_gif.py"
    ],
    "resources": [
      "app/resources/context.txt",
      "app/resources/icon.png"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree has source changes outside generated `skills/`
  artifacts, run `refresh-repo-skill` before relying on API or build details.
- If `app/version.py`, runtime dependencies, provider backend modules, the JSON
  prompt resource, the app entry point, or `build.py` changes, refresh this
  skill even if the commit looks similar.
- If Open Interface later adds package metadata, console entry points, or new
  tests/examples, refresh this skill so routing and verification can include
  them.
