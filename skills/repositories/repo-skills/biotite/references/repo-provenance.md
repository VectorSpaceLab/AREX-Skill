# Repository Provenance

## Purpose

Read this before deciding whether this Biotite skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-29T16:45:12Z",
  "repository": {
    "name": "biotite",
    "remote_url": "https://github.com/biotite-dev/biotite.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "641afc49d68e4a548c2bad8409b405a14e38a3a6",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "biotite",
      "version": "1.7.1",
      "import_names": ["biotite"]
    }
  ],
  "evidence": {
    "source_roots": [
      "src/biotite",
      "src/rust"
    ],
    "docs": [
      "README.rst",
      "doc/install.rst",
      "doc/tutorial",
      "doc/examples/scripts"
    ],
    "examples": [
      "doc/examples/scripts/sequence",
      "doc/examples/scripts/structure"
    ],
    "tests": [
      "tests/sequence",
      "tests/structure",
      "tests/database",
      "tests/application",
      "tests/interface"
    ],
    "configs": [
      "pyproject.toml",
      "setup.py",
      "Cargo.toml",
      "rust-toolchain.toml",
      "environment.yml",
      "pixi.lock"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and the dirty paths differ from this snapshot, run `refresh-repo-skill`.
- If package metadata, public import modules, optional dependency groups, file-format APIs, database/application wrappers, or interface modules changed even on the same commit, run `refresh-repo-skill`.
- The package version above records the wheel used for live API smoke checks; the repository source/docs/tests named above were also used as evidence for current checkout coverage.
