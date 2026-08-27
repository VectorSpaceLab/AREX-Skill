# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Graphify. If the current repo commit, dirty state, package version, public entry points, optional extras, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before making detailed claims.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T10:52:06Z",
  "repository": {
    "name": "graphify",
    "remote_url": "https://github.com/Graphify-Labs/graphify.git",
    "vcs": "git",
    "branch": "v8",
    "tag": "v0.9.39",
    "commit": "50556baaea803e191947fdfcc2e0c22e2d4eb74d",
    "working_tree": "clean-before-skill-artifacts",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "graphifyy",
      "version": "0.9.39",
      "import_names": ["graphify"],
      "entry_points": ["graphify", "graphify-mcp"]
    }
  ],
  "evidence": {
    "source_roots": [
      "graphify",
      "graphify/extractors",
      "graphify/exporters"
    ],
    "docs": [
      "README.md",
      "ARCHITECTURE.md",
      "SECURITY.md",
      "docs/how-it-works.md",
      "docs/node-summaries-rfc.md"
    ],
    "packaged_skills": [
      "graphify/skill.md",
      "graphify/skill-*.md",
      "graphify/skills/*/references/*.md",
      "graphify/always_on/*.md"
    ],
    "tests": [
      "tests",
      "tests/fixtures"
    ],
    "tools_and_scripts": [
      "tools/skillgen",
      "scripts/gen_demo_path.py"
    ],
    "configs": [
      "pyproject.toml",
      ".github/workflows/ci.yml",
      ".github/workflows/publish.yml",
      ".github/workflows/release-graph.yml"
    ],
    "example_outputs_reference_only": [
      "worked"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If the current checkout is dirty in source, docs, package metadata, packaged skills, tests, or CLI entry-point files and the dirty paths differ from this snapshot, refresh the skill.
- If `pyproject.toml` changes `project.name`, `version`, `requires-python`, dependencies, optional extras, or console scripts, refresh the skill.
- If `graphify --help`, `graphify-mcp --help`, or public APIs in `graphify.detect`, `graphify.extract`, `graphify.build`, `graphify.export`, `graphify.serve`, or `graphify.install` changed, refresh the skill.
- If Graphify's packaged assistant skill layout (`graphify/skill*.md`, `graphify/skills/*/references/`, `graphify/always_on/`) changes, refresh the agent-integration sub-skill.

This file intentionally omits local checkout paths, private environment paths, Python executables, cache directories, and install locations.
