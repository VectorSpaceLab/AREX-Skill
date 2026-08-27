# Repository Provenance

## Purpose

Read this before deciding whether the EverOS repo skill is current for a checkout. If the current repository commit, package version, public entry points, CLI/API shape, or major evidence paths differ from this snapshot, refresh the skill before relying on detailed guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T15:28:09Z",
  "repository": {
    "name": "EverOS",
    "remote_url": "https://github.com/EverMind-AI/EverOS.git",
    "vcs": "git",
    "branch": "main",
    "tag": "v1.2.3",
    "commit": "48fc9084888bc17100053227284f939a5aca5e91",
    "working_tree": "clean-at-evidence-capture",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "everos",
      "version": "1.2.3",
      "import_names": ["everos"],
      "python": ">=3.12",
      "console_scripts": ["everos = everos.entrypoints.cli.main:app"],
      "optional_extras": ["multimodal", "otel"]
    }
  ],
  "evidence": {
    "source_roots": ["src/everos"],
    "package_metadata": ["pyproject.toml", "uv.lock"],
    "docs": [
      "README.md",
      "QUICKSTART.md",
      "docs/api.md",
      "docs/cli.md",
      "docs/configuration.md",
      "docs/storage_layout.md",
      "docs/how-memory-works.md",
      "docs/cascade_runbook.md",
      "docs/knowledge.md",
      "docs/multimodal.md",
      "docs/prompt_slots.md",
      "docs/reflection.md",
      "docs/everos-demo.md"
    ],
    "examples": ["examples/langfuse"],
    "scripts": ["scripts/dump_openapi.py", "scripts/e2e_memorize/run.py", "scripts/check_consistency.py"],
    "tests": ["tests/unit", "tests/integration", "tests/e2e"],
    "excluded": ["benchmarks", "use-cases", ".github", ".claude", "maintainer-only check scripts", "large fixtures"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale.
- If public routes, CLI commands, settings sections, dependency extras, or storage layout changed, refresh even when the version string is unchanged.
- The generated `skills/` production output itself is not source evidence; do not treat its presence as a reason to change this snapshot.
