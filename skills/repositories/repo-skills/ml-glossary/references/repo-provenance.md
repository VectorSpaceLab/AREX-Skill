# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of ML Glossary. If the current repo commit, dirty state, package metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on this runtime for repository-specific maintenance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T06:15:00Z",
  "repository": {
    "name": "ml-glossary",
    "remote_url": "https://github.com/bfortuner/ml-glossary.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "ad889a823beee92b7ac1e8c92e85a8ed57d64994",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "The dirty path is generated skill and review output from the production run. Source evidence files were otherwise read from the recorded commit."
  },
  "packages": [],
  "package_notes": "No installable Python package metadata was present. The repository is a Sphinx documentation project with illustrative Python snippets under code/.",
  "evidence": {
    "source_roots": [
      "code/"
    ],
    "docs": [
      "README.md",
      "docs/index.rst",
      "docs/*.rst",
      "docs/conf.py",
      "docs/Makefile"
    ],
    "examples": [
      "code/*.py",
      "notebooks/rnn.ipynb"
    ],
    "tests": [],
    "configs": [
      "docs/conf.py"
    ],
    "excluded": [
      ".git/",
      ".vscode/",
      "docs/_build/",
      "docs/images/",
      "docs/figures/",
      "skills/tests/"
    ]
  },
  "verification_baseline": {
    "required_backend": "cpu",
    "environment_status": "ok",
    "native_case": "Sphinx docs build was the selected repository-native verification; project tests, lint, and formatter were intentionally not selected."
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` in a current checkout differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If source documentation, code snippets, Sphinx configuration, contribution guidance, or public resource catalogs changed, refresh the skill even if the commit is otherwise close.
- If a future checkout adds package metadata, tests, CLI entry points, notebooks with real content, or modernized examples, refresh the environment and verification plan.
- Do not copy local environment paths, Python executable paths, or generation checkout paths into public skill content.
