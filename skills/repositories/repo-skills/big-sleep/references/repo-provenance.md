# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T21:20:00Z",
  "repository": {
    "name": "big-sleep",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "49b20f9c8169667395b68d1bbe169d28137fea8e",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "big-sleep",
      "version": "0.9.1",
      "import_names": ["big_sleep"]
    }
  ],
  "evidence": {
    "source_roots": ["big_sleep"],
    "docs": ["README.md"],
    "examples": [],
    "tests": ["test/multi_prompt_minmax.py"],
    "configs": []
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and the current dirty paths differ, run `refresh-repo-skill`.
- If package metadata or public entry points changed even on the same commit, run `refresh-repo-skill`.

## Evidence notes

- Runtime behavior and signatures were verified against the installed `big_sleep` package from the local source tree and CUDA-enabled torch stack.
- The repository has no separate docs or examples directory; the README and `test/multi_prompt_minmax.py` carry the main user-facing evidence.
