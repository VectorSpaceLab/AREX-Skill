# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of TRL. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-skill-from-repo`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T00:00:00Z",
  "repository": {
    "name": "trl",
    "remote_url": "https://github.com/huggingface/trl",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "4d10b20bf69314f231241cf8267a67c3241137f0",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "trl",
      "version": "1.7.0.dev0",
      "import_names": ["trl"]
    }
  ],
  "evidence": {
    "source_roots": ["trl"],
    "docs": ["README.md", "docs/source"],
    "examples": ["examples/scripts", "examples/cli_configs", "examples/accelerate_configs", "examples/datasets", "examples/notebooks/README.md"],
    "tests": ["tests", "tests/experimental", "tests/distributed", "tests/invariant/README.md"],
    "configs": ["pyproject.toml", "VERSION", "MANIFEST.in", "examples/accelerate_configs", "examples/cli_configs"],
    "repo_guidance": ["AGENTS.md", "CONTRIBUTING.md", "MIGRATION.md", "docs/source/paper_index.md"],
    "existing_skills": ["trl/skills/trl-training/SKILL.md"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-skill-from-repo`.
- If the current working tree dirty paths differ from `repository.dirty_paths`, run `refresh-skill-from-repo` before relying on this skill for changed code.
- If package metadata, public trainer signatures, CLI entry points, optional extras, or environment integrations changed, run `refresh-skill-from-repo` even on the same commit.
- The dirty path `skills/` was created by DisCo generation and is not TRL source behavior evidence.
