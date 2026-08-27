# Repository Provenance

Read this before deciding whether the NAVSIM operating graph matches a newer
checkout. If the commit, package metadata, working-tree baseline, or major
evidence paths differ, refresh the graph instead of trusting old details.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-22T03:15:00Z",
  "repository": {
    "name": "navsim",
    "remote_url": "https://github.com/autonomousvision/navsim",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "0a380a9063d7162ec93d0f51e9990ebac585f720",
    "working_tree": "clean at source snapshot",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "navsim",
      "version": "2.0.0",
      "import_names": ["navsim"]
    },
    {
      "name": "nuplan-devkit",
      "version": "1.2.0 source pin",
      "import_names": ["nuplan"]
    }
  ],
  "evidence": {
    "source_roots": ["navsim"],
    "docs": ["README.md", "docs"],
    "examples": ["tutorial/tutorial_visualization.ipynb"],
    "tests": [],
    "configs": ["navsim/planning/script/config"],
    "scripts": ["scripts", "download"]
  }
}
```

## Refresh check

- Compare `git rev-parse HEAD` with the recorded commit before using source
  details from a checkout.
- Compare package version and public import paths from `setup.py` and the
  installed distribution.
- Check whether `navsim/common`, `navsim/agents`,
  `navsim/planning/script/config`, `docs`, `scripts`, or `download` changed.
- The source snapshot had no repository-owned test directory. Native examples
  and runners were classified as verification candidates instead.
- The generated skill directory and its review artifacts are construction
  outputs, not source evidence; do not treat their presence as proof that the
  package source is unchanged.
