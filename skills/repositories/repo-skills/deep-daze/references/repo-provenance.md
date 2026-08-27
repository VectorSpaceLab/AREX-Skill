# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, public
entry points, or major evidence paths differ from this snapshot, run
`refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T04:10:34Z",
  "repository": {
    "name": "deep-daze",
    "remote_url": "https://github.com/lucidrains/deep-daze.git",
    "vcs": "git",
    "branch": "main",
    "tag": "0.11.1",
    "commit": "c3c471e63c30ccabfd8dfc09ced3028a8979ebe4",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "The only observed dirty path during generation was the untracked skills/ production output area."
  },
  "packages": [
    {
      "name": "deep-daze",
      "version": "0.11.1",
      "import_names": [
        "deep_daze"
      ],
      "console_scripts": [
        "imagine = deep_daze.cli:main"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "deep_daze/"
    ],
    "docs": [
      "README.md"
    ],
    "examples": [
      "README.md embedded commands",
      "samples/ image evidence"
    ],
    "tests": [],
    "configs": [],
    "metadata": [
      "setup.py",
      "MANIFEST.in"
    ],
    "excluded_runtime_payloads": [
      "samples/ binary images",
      "instruction_images/ screenshots",
      ".github/workflows/python-publish.yml release workflow",
      "skills/tests/ review artifacts"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree has source, README, package metadata, CLI, or
  package-data changes that are not represented above, refresh the skill.
- If the public package version, console entry point, CLIP model registry,
  `Imagine` signature, or CLI flags changed, refresh the skill even on the same
  commit.
- If a future checkout adds tests, examples, docs, or scripts that cover new
  Deep Daze workflows, refresh so the skill can use that evidence.
