# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of TorchDrug. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-29T18:51:58Z",
  "repository": {
    "name": "torchdrug",
    "remote_url": "https://github.com/DeepGraphLearning/torchdrug",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "6066fbd82360abb5f270cba1eca560af01b8cc90",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "torchdrug",
      "version": "0.2.1",
      "import_names": ["torchdrug"]
    }
  ],
  "evidence": {
    "source_roots": ["torchdrug"],
    "docs": ["README.md", "doc/source"],
    "examples": ["doc/source/tutorials", "doc/source/quick_start.rst"],
    "tests": ["test"],
    "configs": ["setup.py", "requirements.txt", "conda/torchdrug/meta.yaml"],
    "assets_used_as_evidence": ["asset"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the dirty paths differ beyond generated skill artifacts, run `refresh-repo-skill`.
- If package metadata, Python support, dependencies, public task/model names, dataset constructors, or training engine behavior changes, run `refresh-repo-skill`.
