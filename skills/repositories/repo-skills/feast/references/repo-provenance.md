# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a Feast checkout. If the current repo commit, dirty state, package version, entry points, or major evidence paths differ from this snapshot, run `refresh-skill-from-repo`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T00:00:00Z",
  "repository": {
    "name": "feast",
    "remote_url": "https://github.com/feast-dev/feast",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "eb042f04f5d9bdd7dafbaf654d5b5ec2a2572d9f",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": [
      "skills/disco/",
      "skills/tests/"
    ]
  },
  "packages": [
    {
      "name": "feast",
      "version": "0.1.dev1+geb042f04f",
      "import_names": ["feast"],
      "entry_points": ["feast = feast.cli.cli:cli"]
    }
  ],
  "evidence": {
    "metadata": ["pyproject.toml", "sdk/python/pyproject.toml", "MANIFEST.in", "Makefile", "pixi.lock"],
    "source_roots": ["sdk/python/feast"],
    "docs": ["README.md", "docs/getting-started", "docs/reference", "docs/how-to-guides", "docs/tutorials", "docs/adr"],
    "examples": ["examples"],
    "tests": ["sdk/python/tests/unit", "sdk/python/tests/integration"],
    "existing_skills": ["skills/feast-user-guide", "skills/feast-dev", "skills/feast-architecture", "skills/feast-testing", "skills/references"],
    "scripts": ["scripts", "infra/scripts"],
    "supporting_components": ["protos", "go", "java", "infra/feast-operator", "ui"]
  },
  "inspection": {
    "verified_imports": ["feast", "feast.cli.cli", "feast.repo_config"],
    "verified_cli_checks": ["feast --help", "feast version"],
    "verified_scope": "core local SDK and CLI without optional cloud, GPU, Kubernetes, docs, dev, or benchmark extras"
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If the current working tree has non-generated dirty paths that differ from this snapshot, refresh before relying on API or CLI details.
- If `pyproject.toml`, `sdk/python/feast/cli/cli.py`, `sdk/python/feast/feature_store.py`, feature definition classes, store/provider modules, server modules, docs, examples, or tests changed materially, refresh the skill.
- If the installed Feast package version or console entry point differs from the snapshot, refresh live API and CLI references.

## Evidence Boundaries

This skill distills source, docs, examples, tests, and existing repo-local skills into self-contained runtime guidance. Runtime instructions link only inside this generated skill tree. Original repo paths in this provenance are evidence paths for future refresh decisions, not files that future agents must open to use the skill.
