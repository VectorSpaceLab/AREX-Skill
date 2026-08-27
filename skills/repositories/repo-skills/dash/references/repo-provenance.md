# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a Dash checkout. If
the current repo commit, dirty state, package version, generated component
wrapper behavior, or major evidence paths differ from this snapshot, run a repo
skill refresh before relying on maintainer-specific details.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T14:52:00Z",
  "repository": {
    "name": "dash",
    "remote_url": "https://github.com/plotly/dash.git",
    "vcs": "git",
    "branch": "dev",
    "tag": null,
    "commit": "8ee87c52fefff3e4d550c5b1236b8f1eda574fca",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "dash",
      "version": "4.4.1",
      "import_names": ["dash"]
    }
  ],
  "evidence": {
    "source_roots": [
      "dash",
      "dash/backends",
      "dash/background_callback",
      "dash/development",
      "dash/testing",
      "dash/mcp",
      "dash/dash-renderer/src",
      "components/dash-core-components",
      "components/dash-html-components",
      "components/dash-table"
    ],
    "docs": [
      "README.md",
      "CONTRIBUTING.md",
      "MAKE_A_NEW_BACK_END.md",
      ".ai/README.md",
      ".ai/COMMANDS.md",
      ".ai/ARCHITECTURE.md",
      ".ai/RENDERER.md",
      ".ai/COMPONENTS.md",
      ".ai/TESTING.md",
      ".ai/TROUBLESHOOTING.md",
      ".github/copilot-instructions.md"
    ],
    "package_metadata": [
      "setup.py",
      "requirements/install.txt",
      "requirements/testing.txt",
      "requirements/diskcache.txt",
      "requirements/celery.txt",
      "requirements/fastapi.txt",
      "requirements/quart.txt",
      "requirements/async.txt",
      "requirements/dev.txt",
      "MANIFEST.in",
      "package.json",
      "dash/dash-renderer/package.json",
      "components/dash-core-components/package.json",
      "components/dash-html-components/package.json",
      "components/dash-table/package.json"
    ],
    "tests": [
      "tests/unit",
      "tests/integration",
      "tests/backend_tests",
      "tests/async_tests",
      "tests/background_callback",
      "tests/websocket",
      "dash/dash-renderer/tests",
      "components/dash-core-components/tests",
      "components/dash-html-components/tests",
      "components/dash-table/tests"
    ],
    "configs": [
      "pytest.ini",
      ".flake8",
      ".pylintrc",
      ".lintstagedrc.js",
      ".nvmrc"
    ]
  }
}
```

## Verified baseline facts

- Python package version: `4.4.1`.
- Public imports checked for this baseline: `Dash`, `html.Div`, `dcc.Graph`,
  `Input`, `Output`, `State`, `callback`, `clientside_callback`, and `Patch`.
- Backend factory checks passed for Flask, FastAPI, and Quart when the relevant
  optional dependencies were installed.
- CLI help checks passed for `dash-generate-components`,
  `dash-update-components`, and `renderer`.
- This checkout initially required component wrapper generation before
  `dash.html.Div` and `dash.dcc.Graph` could be imported from the editable
  install. If a future checkout has prebuilt wrappers or a released wheel, that
  detail may differ.

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as
  potentially stale and refresh it.
- If public entry points in package metadata, optional extras, or generated
  component package layout changed, refresh even if the commit is close.
- If a maintainer task depends on exact renderer callback scheduling, backend
  adapter methods, generated component metadata, or testing fixtures, verify
  those source files against the current checkout before editing.
- For ordinary app-use tasks against a released Dash version, prefer live
  package inspection when the installed version differs from `4.4.1`.
