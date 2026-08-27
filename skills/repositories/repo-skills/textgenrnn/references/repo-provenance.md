# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T19:59:58Z",
  "repository": {
    "name": "textgenrnn",
    "remote_url": "https://github.com/minimaxir/textgenrnn.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "ee8b9e806d109c25566581f358a4a72b6f03929a",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "textgenrnn",
      "version": "2.0.0",
      "import_names": ["textgenrnn"]
    }
  ],
  "evidence": {
    "source_roots": ["textgenrnn"],
    "docs": ["README.md", "docs", "datasets/README.md", "weights/README.md", "outputs/README.md"],
    "examples": ["docs"],
    "tests": [],
    "configs": ["setup.py", "setup.cfg", "requirements.txt", "MANIFEST.in"],
    "assets": ["textgenrnn/textgenrnn_weights.hdf5", "textgenrnn/textgenrnn_vocab.json", "weights", "datasets", "outputs"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ materially, run `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit, run `refresh-repo-skill`.

## Snapshot notes

The repository was already dirty because a repo-local `skills/` production/log area existed. The generated skill itself is stored under `skills/` during this construction run and is not an original package source root.
