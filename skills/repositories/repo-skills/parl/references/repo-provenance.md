# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of PARL. If the current repo commit, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T19:37:31Z",
  "repository": {
    "name": "PARL",
    "remote_url": "https://github.com/PaddlePaddle/PARL.git",
    "vcs": "git",
    "branch": "develop",
    "tag": null,
    "commit": "fb5e5a707f6466bca7cf4124eccd57b65fb2d9c3",
    "working_tree": "clean-at-source-capture",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "parl",
      "version": "2.2.1",
      "import_names": ["parl"]
    }
  ],
  "evidence": {
    "source_roots": ["parl"],
    "docs": ["README.md", "README.cn.md", "docs"],
    "examples": ["examples", "waymax_rl", "evo_kit"],
    "tests": ["parl/core/tests", "parl/env/tests", "parl/utils/tests", "parl/remote/tests", "parl/algorithms"],
    "configs": ["test_tipc/configs", "waymax_rl/conf"],
    "scripts": ["test_tipc", "evo_kit/scripts", "examples/NeurIPS2019-Learn-to-Move-Challenge/scripts"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, console entry points, backend selection behavior, or public algorithm exports changed, run `refresh-repo-skill`.
- If major docs, examples, `waymax_rl`, `evo_kit`, `test_tipc`, or public tests changed, rerun repository-skill verification even if the package version did not change.
- The generated skill files themselves were not part of the source evidence snapshot.
