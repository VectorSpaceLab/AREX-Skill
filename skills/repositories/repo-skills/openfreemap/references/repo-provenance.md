# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of OpenFreeMap. If the current repo commit, dirty state, package version, or evidence roots differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T07:20:25Z",
  "repository": {
    "name": "openfreemap",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "8892fc6e1dd7433826c9e9b88f3b9915c7e7e135",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "ssh_lib",
      "version": "0.0.0",
      "import_names": ["ssh_lib"]
    },
    {
      "name": "http_host_lib",
      "version": "0.0.0",
      "import_names": ["http_host_lib"]
    },
    {
      "name": "tile_gen_lib",
      "version": "0.0.0",
      "import_names": ["tile_gen_lib"]
    },
    {
      "name": "loadbalancer_lib",
      "version": "0.0.0",
      "import_names": ["loadbalancer_lib"]
    }
  ],
  "evidence": {
    "source_roots": [
      "ssh_lib",
      "modules/http_host",
      "modules/tile_gen",
      "modules/loadbalancer"
    ],
    "docs": [
      "README.md",
      "docs/self_hosting.md",
      "docs/dev_setup.md",
      "docs/debugging_names.md",
      "docs/benchmark"
    ],
    "examples": [
      "website/src/content/how_to_use"
    ],
    "tests": [],
    "configs": [
      "config"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty state differs from this snapshot, run `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit, run `refresh-repo-skill`.
