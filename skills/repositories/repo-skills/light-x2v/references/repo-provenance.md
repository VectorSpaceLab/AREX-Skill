# Repository Provenance

This snapshot records the repository state used to build the LightX2V skill graph.
Future refreshes should compare the current checkout against this file before reusing the skill.

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T23:28:48Z",
  "repository": {
    "name": "LightX2V",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "b9cd165ef6bb0554ff65edc872b3768f8bc613b0",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "lightx2v",
      "version": "0.1.0",
      "import_names": [
        "lightx2v",
        "lightx2v_platform",
        "lightx2v_train"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "lightx2v",
      "lightx2v_platform",
      "lightx2v_train"
    ],
    "docs": [
      "README.md",
      "docs/EN/source"
    ],
    "examples": [
      "examples"
    ],
    "tests": [
      "examples/worldmirror/test_worldmirror.py",
      "examples/worldplay"
    ],
    "configs": [
      "configs"
    ],
    "scripts": [
      "scripts"
    ],
    "tools": [
      "tools"
    ],
    "ui": [
      "app"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` changes, treat this skill as potentially stale.
- If the working tree becomes dirty in additional paths, update the `dirty_paths` list or replace it with a short summary before publishing a refresh.
- If package imports, public CLIs, or workflow entry points change, refresh the skill even when the commit stays the same.
