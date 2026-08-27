# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the Transformer Lab application repository. If the current repo commit, dirty state, package versions, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T17:07:24Z",
  "repository": {
    "name": "transformerlab-app",
    "remote_url": "https://github.com/transformerlab/transformerlab-app.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "db4ce30840db7ccbf52d637b15769d454d22cf15",
    "working_tree": "clean-before-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "transformerlab-app",
      "version": "0.40.1",
      "import_names": []
    },
    {
      "name": "transformerlab-api",
      "version": "0.27.0",
      "import_names": ["transformerlab (source-run from api/)"]
    },
    {
      "name": "transformerlab-cli",
      "version": "0.0.68",
      "import_names": ["transformerlab_cli"],
      "entry_points": ["lab"]
    },
    {
      "name": "transformerlab",
      "version": "0.1.46",
      "import_names": ["lab"],
      "entry_points": ["tfl-remote-trap"]
    }
  ],
  "evidence": {
    "source_roots": [
      "src/renderer",
      "api/transformerlab",
      "cli/src/transformerlab_cli",
      "lab-sdk/src/lab"
    ],
    "docs": [
      "README.md",
      "AGENTS.md",
      "docs/frontend.md",
      "docs/backend.md",
      "docs/Auth.md",
      "docs/cli.md",
      "docs/task-execution"
    ],
    "examples": [
      "api/transformerlab/galleries/examples"
    ],
    "tests": [
      "api/test",
      "cli/tests",
      "lab-sdk/tests",
      "test/playwright"
    ],
    "configs": [
      "package.json",
      "api/pyproject.toml",
      "cli/pyproject.toml",
      "lab-sdk/pyproject.toml",
      "playwright.config.ts",
      "docker-compose.test.yml",
      "ruff.toml"
    ],
    "scripts": [
      "scripts/dev.py",
      "scripts/test-task-placement.py",
      "api/install.sh",
      "api/run.sh",
      "api/scripts/create_user.py",
      "api/scripts/remote_setup.sh",
      "scripts/orval/generateSDK.sh"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the snapshot commit, treat the skill as potentially stale and run `refresh-repo-skill`.
- The source checkout was clean when source evidence was captured. Generated files under `skills/` were written after that snapshot and are not source evidence.
- If `package.json`, any `pyproject.toml`, public CLI entry points, task/job schemas, provider interfaces, or frontend API client patterns changed, refresh this skill even if the commit is otherwise close.
- If the target checkout is a fork or private patch stack, compare the changed files against the evidence paths above before relying on exact commands or field names.
