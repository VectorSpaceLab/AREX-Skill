# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a Meshroom checkout. If the current repo commit, dirty state, package version, public entry points, or evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T16:03:25Z",
  "repository": {
    "name": "Meshroom",
    "remote_url": "https://github.com/alicevision/Meshroom.git",
    "vcs": "git",
    "branch": "develop",
    "tag": "nightly",
    "commit": "643231fd7cab94d9ff31f9a36c8588bb23d88db8",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "Meshroom",
      "version": "2026.1.0+develop",
      "import_names": ["meshroom"]
    }
  ],
  "evidence": {
    "source_roots": [
      "meshroom",
      "meshroom/core",
      "meshroom/core/desc",
      "meshroom/core/plugins",
      "meshroom/nodes/general",
      "meshroom/ui",
      "meshroom/submitters/localFarm",
      "localfarm"
    ],
    "docs": [
      "README.md",
      "INSTALL.md",
      "INSTALL_PLUGINS.md",
      "NODE_DEVELOPMENT.md",
      "docs/README.md",
      "docs/source"
    ],
    "clis": [
      "bin/meshroom_batch",
      "bin/meshroom_compute",
      "bin/meshroom_createChunks",
      "bin/meshroom_info",
      "bin/meshroom_localfarm",
      "bin/meshroom_newNodeType",
      "bin/meshroom_statistics",
      "bin/meshroom_status",
      "bin/meshroom_submit"
    ],
    "tests": [
      "tests/test_graph.py",
      "tests/test_graphIO.py",
      "tests/test_compatibility.py",
      "tests/test_compute.py",
      "tests/test_nodes.py",
      "tests/test_plugins.py",
      "tests/test_submit.py",
      "tests/test_pipeline.py",
      "tests/test_nodeCommandLineFormatting.py",
      "tests/test_attribute*.py",
      "tests/plugins"
    ],
    "configs": [
      "setup.py",
      "requirements.txt",
      "dev_requirements.txt",
      ".github/workflows",
      "tests/plugins/meshroom/config.json"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current dirty paths differ from `dirty_paths`, refresh before relying on repository-specific guidance.
- If package metadata, `requirements.txt`, CLI entry points, plugin loading, graph serialization format, or public node descriptor APIs changed, refresh even on the same commit.
- If external AliceVision plugin packaging changed, refresh only the external-plugin parts of the guidance; Meshroom core framework routes may still be valid.
