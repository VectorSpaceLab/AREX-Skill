# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the Towhee repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T18:50:00Z",
  "repository": {
    "name": "towhee",
    "remote_url": "https://github.com/towhee-io/towhee.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "fe856301680713032e9613cf2500932f0ae3ad13",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "towhee",
      "version": "1.1.3",
      "import_names": ["towhee"]
    },
    {
      "name": "towhee.models",
      "version": "1.1.3",
      "import_names": ["towhee.models"],
      "selected_scope": "optional overview only; per-model APIs are not exhaustively covered"
    }
  ],
  "evidence": {
    "source_roots": [
      "towhee",
      "towhee/runtime",
      "towhee/operator",
      "towhee/datacollection",
      "towhee/command",
      "towhee/serve",
      "towhee/trainer",
      "towhee/types",
      "towhee/tools"
    ],
    "docs": [
      "README.md",
      "docs/02-Getting Started",
      "docs/03-User Guides/01-Pipeline Programing Guide",
      "docs/04-Triton Server",
      "docs/05-API Reference",
      "towhee/command/README.md",
      "towhee/models/README.md"
    ],
    "examples": [],
    "tests": [
      "tests/unittests/runtime",
      "tests/unittests/datacollection",
      "tests/unittests/types",
      "tests/unittests/command",
      "tests/unittests/serve",
      "tests/unittests/trainer"
    ],
    "configs": [
      "setup.cfg",
      "setup.py",
      "requirements.txt",
      "test_requirements.txt",
      "MANIFEST.in"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, console entry points, or public imports change even on the same commit, refresh the skill.
- If Towhee changes its packaging around `pkg_resources`, Pydantic, `towhee.models`, service dependencies, or training auto-install behavior, refresh the install/troubleshooting references.
- If a user asks for exhaustive per-model coverage under `towhee.models`, extend this skill rather than relying on the optional overview here.
