# Repository Provenance

## Purpose

Read this before deciding whether this skill matches the current checkout of TensorLayer. If the current repository commit, branch, working-tree state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T18:35:55Z",
  "repository": {
    "name": "TensorLayer",
    "remote_url": "https://github.com/tensorlayer/TensorLayer.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "0681633252667b317a23b803c11a8a060a44bf31",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "tensorlayer",
      "version": "2.2.4",
      "import_names": [
        "tensorlayer"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "tensorlayer"
    ],
    "docs": [
      "README.md",
      "README.rst",
      "docs"
    ],
    "examples": [
      "examples"
    ],
    "tests": [
      "tests"
    ],
    "configs": [
      "setup.py",
      "setup.cfg",
      "requirements"
    ],
    "scripts": [
      "scripts",
      "tl"
    ]
  }
}
```
