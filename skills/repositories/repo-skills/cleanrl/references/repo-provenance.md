# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a CleanRL checkout. If the current commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "evidence": {
    "docs": [
      "README.md",
      "docs/get-started",
      "docs/rl-algorithms",
      "docs/advanced",
      "docs/cloud",
      "docs/contribution.md"
    ],
    "metadata": [
      "pyproject.toml",
      "requirements",
      "uv.lock",
      "mkdocs.yml",
      ".pre-commit-config.yaml"
    ],
    "scripts_and_operations": [
      "benchmark",
      "cloud",
      "Dockerfile",
      "entrypoint.sh",
      "tuner_example.py"
    ],
    "source_roots": [
      "cleanrl",
      "cleanrl_utils"
    ],
    "tests": [
      "tests"
    ]
  },
  "generated_at_utc": "2026-06-23T00:00:00Z",
  "packages": [
    {
      "import_names": [
        "cleanrl",
        "cleanrl_utils"
      ],
      "name": "cleanrl",
      "version": "2.0.0b1"
    }
  ],
  "repository": {
    "branch": "master",
    "commit": "fe8d8a03c41a7ef5b523e2e354bd01c363e786bb",
    "dirty_paths": [],
    "name": "cleanrl",
    "note": "Working tree was clean before this generated skills/ output was created.",
    "remote_url": "https://github.com/vwxyzjn/cleanrl",
    "tag": null,
    "vcs": "git",
    "working_tree": "clean-before-skill-generation"
  },
  "schema": "disco.repo-provenance.v1"
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has source, docs, metadata, or test changes not represented here, run `refresh-repo-skill`.
- If CleanRL package metadata, script flags, optional extras, or utility entry points changed, run `refresh-repo-skill` even on the same branch.
- The generated `skills/` output is not part of the upstream source baseline.
