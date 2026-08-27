# Repository Provenance

## Purpose

Read this before deciding whether the bundled `runtime/source/` snapshot is current for MuZero General. If the upstream commit, dirty state, package metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill` and rebuild the bundled source manifest.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-19T00:00:00Z",
  "repository": {
    "name": "muzero-general",
    "remote_url": "https://github.com/werner-duvaud/muzero-general.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "0825bd544fc172a2e2dcc96d43711123222c4a2f",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "bundled_source": {
    "path": "runtime/source",
    "manifest": "runtime/source/BUNDLED-SOURCE-MANIFEST.json",
    "default_for_helpers": true,
    "external_checkout_required_for_core_workflows": false
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": [
        "muzero",
        "models",
        "self_play",
        "replay_buffer",
        "trainer",
        "shared_storage",
        "diagnose_model",
        "games"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "muzero.py",
      "models.py",
      "self_play.py",
      "trainer.py",
      "replay_buffer.py",
      "shared_storage.py",
      "diagnose_model.py",
      "games/"
    ],
    "docs": [
      "README.md",
      "docs/README.md",
      "notebook.ipynb"
    ],
    "examples": [
      "games/*.py",
      "notebook.ipynb"
    ],
    "tests": [
      ".github/workflows/ci-testing.yaml"
    ],
    "configs": [
      "games/*:MuZeroConfig",
      "requirements.txt",
      "requirements.lock"
    ],
    "runtime_copy_includes": [
      "runtime/source/*.py",
      "runtime/source/games/*.py",
      "runtime/source/requirements.txt",
      "runtime/source/requirements.lock",
      "runtime/source/README.md",
      "runtime/source/docs/README.md",
      "runtime/source/.github/workflows/ci-testing.yaml",
      "runtime/source/BUNDLED-SOURCE-MANIFEST.json"
    ],
    "excluded_from_runtime_copy": [
      "docs/*.png",
      "results/*/model.checkpoint",
      "generated skill/test artifacts under skills/",
      ".git/**"
    ]
  }
}
```

## Refresh Check

- If the upstream `git rev-parse HEAD` differs from `repository.commit`, treat the bundled source as potentially stale and run `refresh-repo-skill`.
- If public source files, game modules, requirements, or the CLI/API in `muzero.py` changed, run `refresh-repo-skill` and rebuild `runtime/source/BUNDLED-SOURCE-MANIFEST.json`.
- The dirty path recorded here is the generated `skills/` output area from construction; unrelated future dirty source paths should trigger a refresh review.
- This upstream project has no Python distribution metadata; if a future version adds packaging or changes import roots, refresh the skill and adjust the bundled entry points.
