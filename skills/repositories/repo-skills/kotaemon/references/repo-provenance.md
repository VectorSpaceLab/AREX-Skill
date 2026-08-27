# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Kotaemon. If the current repo commit, dirty state, package metadata, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-30T00:00:00Z",
  "repository": {
    "name": "kotaemon",
    "remote_url": "https://github.com/Cinnamon/kotaemon.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "9ad3e4e49aa35b8acddd235918a5d9753c1cfdf9",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "kotaemon-app",
      "version": null,
      "import_names": []
    },
    {
      "name": "kotaemon",
      "version": "0.0.1",
      "import_names": ["kotaemon"]
    },
    {
      "name": "ktem",
      "version": "0.0.1",
      "import_names": ["ktem"]
    }
  ],
  "evidence": {
    "source_roots": [
      "libs/kotaemon/kotaemon",
      "libs/ktem/ktem",
      "app.py",
      "flowsettings.py"
    ],
    "docs": [
      "README.md",
      "docs/usage.md",
      "docs/online_install.md",
      "docs/local_model.md",
      "docs/development",
      "docs/pages/app",
      "docs/integrations"
    ],
    "examples": [
      "templates/project-default",
      "templates/component-default"
    ],
    "tests": [
      "libs/kotaemon/tests",
      "libs/ktem/ktem_tests"
    ],
    "configs": [
      "pyproject.toml",
      "libs/kotaemon/pyproject.toml",
      "libs/ktem/pyproject.toml",
      ".env.example",
      "settings.yaml.example",
      "mkdocs.yml"
    ],
    "scripts": [
      "scripts/run_linux.sh",
      "scripts/run_macos.sh",
      "scripts/run_windows.bat",
      "scripts/update_linux.sh",
      "scripts/update_macos.sh",
      "scripts/update_windows.bat",
      "scripts/serve_local.py",
      "scripts/download_pdfjs.sh",
      "scripts/migrate/migrate_chroma_db.py"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If dirty paths differ in a way that affects source, docs, scripts, tests, package metadata, examples, or configs, refresh the skill.
- If package dependencies, public entry points, app settings, provider configuration keys, loader classes, index contracts, or extension protocols changed, refresh the skill even on the same commit.
- Generated `skills/` output was the only dirty path recorded during this snapshot; do not treat that alone as source drift.
