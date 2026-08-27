# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of SimpleTuner. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T08:49:19Z",
  "repository": {
    "name": "SimpleTuner",
    "remote_url": "https://github.com/bghira/SimpleTuner.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "c313cc3d97066da29ef8b6dacf3d33e7853f527a",
    "working_tree": "clean-before-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "simpletuner",
      "version": "4.7.0",
      "import_names": ["simpletuner"],
      "entry_points": [
        "simpletuner",
        "simpletuner-train",
        "simpletuner-configure",
        "simpletuner-inference"
      ]
    }
  ],
  "evidence": {
    "source_roots": ["simpletuner", "st_cli.py"],
    "package_metadata": ["pyproject.toml", "setup.py", "MANIFEST.in"],
    "docs": [
      "README.md",
      "documentation/INSTALL.md",
      "documentation/TUTORIAL.md",
      "documentation/QUICKSTART.md",
      "documentation/OPTIONS.md",
      "documentation/DATALOADER.md",
      "documentation/webui",
      "documentation/api",
      "documentation/experimental",
      "documentation/quickstart",
      "documentation/distillation",
      "documentation/evaluation"
    ],
    "examples": ["simpletuner/examples", "config"],
    "scripts": ["scripts"],
    "tests": ["tests"],
    "repo_guidance": ["AGENTS.md", "CLAUDE.md", "GEMINI.md"]
  },
  "verified_package_facts": {
    "python_range": ">=3.12,<3.14",
    "model_family_count": 41,
    "packaged_example_count": 110,
    "cli_help_commands": [
      "train",
      "examples",
      "configure",
      "server",
      "shutdown",
      "cloud",
      "jobs",
      "quota",
      "notifications",
      "auth",
      "backup",
      "database",
      "metrics",
      "webhooks",
      "worker"
    ]
  }
}
```

`working_tree: clean-before-generation` means the source tree was clean before this generated skill and review artifacts were written. Generated `skills/disco/` and `skills/tests/` outputs are not source evidence dirty paths.

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, public entry points, model metadata, CLI parser commands, documented install variants, or major docs/config/data surfaces changed, run `refresh-repo-skill`.
- If the current checkout has source changes that affect `simpletuner/`, `documentation/`, `config/`, `scripts/`, or `tests/`, refresh before relying on detailed workflow guidance.
- Do not copy local environment paths, private cache paths, or raw command logs into refreshed public provenance.
