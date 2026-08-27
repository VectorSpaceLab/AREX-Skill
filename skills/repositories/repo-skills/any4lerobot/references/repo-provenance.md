# Repository Provenance

Read this before deciding whether this operating skill matches a checkout of
Any4LeRobot. If the commit, dirty state, public entry points, or major evidence
paths differ, refresh the repo skill before relying on its claims.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T19:26:41Z",
  "repository": {
    "name": "any4lerobot",
    "remote_url": "https://github.com/Tavish9/any4lerobot.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "e5f767f39da57be0d3f077ff8935b53803e03395",
    "working_tree": "dirty",
    "dirty_paths": ["skills/ (Creator-generated runtime and review artifacts)"],
    "source_dirty_before_generation": "clean"
  },
  "packages": [
    {
      "name": "any4lerobot",
      "version": null,
      "import_names": [],
      "note": "The repository is a script collection and declares no Python distribution metadata."
    }
  ],
  "evidence": {
    "source_roots": [
      "generic_converter",
      "openx2lerobot",
      "agibot2lerobot",
      "robomind2lerobot",
      "libero2lerobot",
      "robocasa2lerobot",
      "lerobot2rlds",
      "ds_version_convert"
    ],
    "docs": [
      "README.md",
      "generic_converter/README.md",
      "openx2lerobot/README.md",
      "agibot2lerobot/README.md",
      "robomind2lerobot/README.md",
      "libero2lerobot/README.md",
      "robocasa2lerobot/README.md",
      "lerobot2rlds/README.md",
      "ds_version_convert/README.md",
      "ds_version_convert/*/README.md"
    ],
    "examples": [],
    "tests": [],
    "configs": [
      "agibot2lerobot/agibot_utils/config.py",
      "openx2lerobot/oxe_utils/configs.py",
      "robomind2lerobot/robomind_uitls/configs"
    ],
    "scripts": [
      "agibot2lerobot/agibot_h5.py",
      "openx2lerobot/openx_rlds.py",
      "robomind2lerobot/robomind_h5.py",
      "libero2lerobot/libero_h5.py",
      "robocasa2lerobot/robocasa_h5.py",
      "lerobot2rlds/lerobot2rlds.py",
      "ds_version_convert/*/convert_*.py"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `e5f767f39da57be0d3f077ff8935b53803e03395`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the source checkout's dirty paths differ from the generated `skills/`
  artifact note, inspect the source commit and regenerate provenance.
- If Any4LeRobot gains packaging metadata, console entry points, native tests,
  new source converters, or changes LeRobot API assumptions, refresh the owning
  sub-skill and its compatibility references.
- Creator review artifacts are not runtime evidence and must not be copied into
  a published skill.
