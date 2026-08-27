# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an OpenMed checkout.
If the current repo commit, dirty state, package version, public APIs, CLI
commands, or major evidence paths differ from this snapshot, run
`refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T03:08:14Z",
  "repository": {
    "name": "openmed",
    "remote_url": "https://github.com/maziyarpanahi/openmed.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "465921b2597e4bb606395d285809e05ebf0a5ce5",
    "working_tree": "clean at extraction start; generated skill artifacts were written afterward",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "openmed",
      "version": "2.2.0",
      "import_names": ["openmed"]
    }
  ],
  "evidence": {
    "metadata": ["pyproject.toml", "uv.lock", "README.md", "AGENTS.md"],
    "source_roots": [
      "openmed",
      "openmed/core",
      "openmed/processing",
      "openmed/clinical",
      "openmed/structured",
      "openmed/risk",
      "openmed/eval",
      "openmed/compliance",
      "openmed/interop",
      "openmed/service",
      "openmed/mcp",
      "openmed/multimodal",
      "openmed/mlx",
      "openmed/onnx",
      "openmed/coreml",
      "openmed/torch",
      "openmed/ner",
      "openmed/zero_shot"
    ],
    "docs": ["docs", "android/README.md", "swift/OpenMedKit"],
    "examples": ["examples"],
    "tests": ["tests/unit", "tests/integration", "tests/fixtures", "tests/fuzz", "tests/property", "tests/mobile"],
    "configs": ["mkdocs.yml", "Package.swift", "android", "models.jsonl"],
    "existing_repo_skills_as_evidence": ["skills/*/SKILL.md"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If package metadata, optional extras, CLI commands, model manifest shape,
  service schema, or public import signatures changed, refresh even on the same
  commit.
- If a checkout has uncommitted source changes outside generated skill/review
  artifacts, refresh before relying on this skill for that checkout.
- If the user task targets new OpenMedKit, Android, browser, service, model, or
  privacy-risk behavior added after this snapshot, refresh first.
