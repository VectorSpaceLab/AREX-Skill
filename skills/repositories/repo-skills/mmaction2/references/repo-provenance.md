# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of MMAction2. If the current repository commit, dirty source state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T17:26:13Z",
  "repository": {
    "name": "mmaction2",
    "remote_url": "https://github.com/open-mmlab/mmaction2.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "a5a167dff2399e2d182a60332325f9c0d4663517",
    "working_tree": "source-clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "mmaction2",
      "version": "1.2.0",
      "import_names": ["mmaction"]
    }
  ],
  "evidence": {
    "source_roots": [
      "mmaction/"
    ],
    "docs": [
      "README.md",
      "docs/en/get_started/installation.md",
      "docs/en/get_started/quick_run.md",
      "docs/en/user_guides/inference.md",
      "docs/en/user_guides/train_test.md",
      "docs/en/user_guides/prepare_dataset.md",
      "docs/en/user_guides/config.md",
      "docs/en/advanced_guides/customize_dataset.md",
      "docs/en/advanced_guides/customize_models.md",
      "docs/en/advanced_guides/customize_pipeline.md",
      "docs/en/useful_tools.md"
    ],
    "examples": [
      "demo/",
      "projects/README.md",
      "projects/example_project/"
    ],
    "configs": [
      "configs/",
      "model-index.yml",
      "dataset-index.yml"
    ],
    "scripts": [
      "tools/train.py",
      "tools/test.py",
      "tools/analysis_tools/",
      "tools/visualizations/",
      "tools/convert/",
      "tools/deployment/",
      "tools/data/"
    ],
    "tests": [
      "tests/apis/",
      "tests/datasets/",
      "tests/evaluation/",
      "tests/models/",
      "tests/structures/"
    ],
    "package_metadata": [
      "setup.py",
      "setup.cfg",
      "MANIFEST.in",
      "requirements/build.txt",
      "requirements/mminstall.txt",
      "requirements/optional.txt",
      "requirements/tests.txt",
      "requirements/multimodal.txt"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If MMAction2's package version, dependency bounds, public API signatures, registry names, config layout, or train/test command flags changed, run `refresh-repo-skill`.
- If a task depends on optional packages or backend flows not verified in this skill baseline, verify those paths in the user's current environment before relying on them.
- Generated skill files may appear as untracked paths in a source checkout; compare source changes separately from generated skill output.
