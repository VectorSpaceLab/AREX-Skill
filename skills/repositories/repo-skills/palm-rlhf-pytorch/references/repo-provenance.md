# Repository Provenance

## Purpose

Read this before deciding whether this skill matches a checkout of the repository. If the current commit, dirty state, package version, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-13T18:29:10Z",
  "repository": {
    "name": "PaLM-rlhf-pytorch",
    "remote_url": "https://github.com/lucidrains/PaLM-rlhf-pytorch.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "bd0d0f3893ec62f827fa35e759cb38d748829d51",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/disco/palm-rlhf-pytorch/",
      "skills/tests/palm-rlhf-pytorch/"
    ]
  },
  "packages": [
    {
      "name": "PaLM-rlhf-pytorch",
      "version": "0.7.5",
      "import_names": ["palm_rlhf_pytorch"]
    }
  ],
  "evidence": {
    "source_roots": ["palm_rlhf_pytorch"],
    "docs": ["README.md", "data/README.md"],
    "examples": ["examples.py"],
    "tests": [],
    "configs": ["pyproject.toml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and refresh it.
- If the dirty paths change materially, refresh it.
- If package metadata, public imports, or example/training behavior changes, refresh it.

## Evidence Notes

- The repository publishes a single import package, `palm_rlhf_pytorch`, with the public root exports used by this skill.
- The source tree is centered on the `palm_rlhf_pytorch/` package plus `README.md`, `examples.py`, and `train.py`.
- The repo has no dedicated test suite or console entry points in the inspected snapshot.
