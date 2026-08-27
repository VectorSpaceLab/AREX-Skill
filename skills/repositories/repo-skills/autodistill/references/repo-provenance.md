# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Autodistill. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T08:53:51Z",
  "repository": {
    "name": "autodistill",
    "remote_url": "https://github.com/autodistill/autodistill.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "7684d2138804f411359ca9671cb615e176961ae9",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "The package source, docs, and tests were inspected at the commit above; the dirty path is generated skill/review output created during skill construction."
  },
  "packages": [
    {
      "name": "autodistill",
      "version": "0.1.29",
      "import_names": ["autodistill"]
    }
  ],
  "evidence": {
    "source_roots": [
      "autodistill/",
      "autodistill/core/",
      "autodistill/detection/",
      "autodistill/classification/",
      "autodistill/text_classification/"
    ],
    "package_metadata": [
      "setup.py",
      "requirements.txt",
      "autodistill/__init__.py",
      "autodistill/models.csv"
    ],
    "docs": [
      "README.md",
      "docs/quickstart.md",
      "docs/command-line-interface.md",
      "docs/reference/",
      "docs/utilities/",
      "docs/supported-models.md",
      "docs/base_models/",
      "docs/target_models/"
    ],
    "tests": [
      "test/test_hello.py",
      "test/test_load_image.py",
      "test/data/dog.jpeg"
    ],
    "ci": [
      ".github/workflows/test.yml"
    ],
    "excluded_or_deprioritized": [
      "docs/custom_theme/",
      "docs/javascript/",
      "docs/stylesheets/",
      "automation/",
      ".github/workflows/publish.yml",
      ".github/workflows/docs.yml"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, CLI entry points, registry aliases, or public base/target model interfaces changed, run `refresh-repo-skill` even on the same commit.
- If the current working tree has source/doc/test changes outside generated skill output, run `refresh-repo-skill`.
- If plugin packages changed independently, refresh or extend the relevant plugin-specific skill rather than assuming this core Autodistill skill verifies plugin runtime behavior.
