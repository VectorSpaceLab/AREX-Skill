# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, public
signatures, tests, or major evidence paths differ from this snapshot, run
`refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T13:00:03Z",
  "repository": {
    "name": "pytorch-summary",
    "remote_url": "https://github.com/sksq96/pytorch-summary.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "345d898d84507b848e92dab4629e03405e19afce",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "The source files used as evidence were clean; untracked skills/ contains production logs, generated runtime skill files, and review artifacts."
  },
  "packages": [
    {
      "name": "torchsummary",
      "version": "1.5.1",
      "import_names": [
        "torchsummary"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "torchsummary"
    ],
    "docs": [
      "README.md"
    ],
    "examples": [
      "README.md code examples"
    ],
    "tests": [
      "torchsummary/tests/unit_tests/torchsummary_test.py",
      "torchsummary/tests/test_models/test_model.py"
    ],
    "configs": [
      "setup.py"
    ],
    "licenses": [
      "LICENSE"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as
  potentially stale and run `refresh-repo-skill`.
- If source files under `torchsummary/`, `README.md`, `setup.py`, or the tests
  differ from this snapshot, refresh the skill even if the commit is unchanged.
- If the package version, public exports, public signatures, or dependency
  metadata change, refresh the skill.
- If the only dirty paths are generated `skills/` artifacts, they do not by
  themselves change package behavior, but confirm whether a newer generated
  skill already supersedes this one.
