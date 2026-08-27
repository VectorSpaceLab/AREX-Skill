# Repository Provenance

## Purpose

Read this before deciding whether this DGL skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-22T00:00:00Z",
  "repository": {
    "name": "dgl",
    "remote_url": "https://github.com/dmlc/dgl",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "3d16000b4170fa741ed9e9667f22ba84d3493026",
    "working_tree": "dirty-generated-skill-artifacts-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "dgl",
      "version": "2.5-source-checkout",
      "import_names": ["dgl"]
    },
    {
      "name": "dgl",
      "version": "2.1.0-live-inspection-wheel",
      "import_names": ["dgl"]
    },
    {
      "name": "dglgo",
      "version": "0.0.2-source-checkout",
      "import_names": ["dglgo"]
    }
  ],
  "evidence": {
    "source_roots": [
      "python/dgl",
      "dglgo/dglgo",
      "graphbolt",
      "dgl_sparse",
      "src",
      "include",
      "tensoradapter"
    ],
    "docs": [
      "README.md",
      "docs/source",
      "dglgo/README.md"
    ],
    "examples": [
      "examples",
      "tutorials",
      "notebooks"
    ],
    "tests": [
      "tests/python",
      "tests/tools",
      "dglgo/tests"
    ],
    "configs": [
      "CMakeLists.txt",
      "pyproject.toml",
      "python/setup.py",
      "dglgo/setup.py",
      "script/dgl_dev.yml.template",
      "dglgo/recipes"
    ],
    "scripts_and_tools": [
      "script",
      "tools"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has source, docs, examples, tests, packaging, or dependency changes beyond generated skill artifacts, run `refresh-repo-skill`.
- If DGL package metadata, GraphBolt library naming, DGL-Go commands, public APIs, or major evidence paths change, run `refresh-repo-skill` even on the same commit.
- This skill used a released DGL wheel for live import/signature checks because the checkout did not contain built native libraries. Re-run live inspection against a built checkout when refreshing after native API changes.
