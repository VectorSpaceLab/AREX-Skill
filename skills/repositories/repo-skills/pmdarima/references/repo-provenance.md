# Repository provenance

Read this before deciding whether the operating skill matches a checkout. If
the commit, tag, package metadata, public entry points, or major evidence paths
differ, use `refresh-repo-skill` rather than assuming the graph is current.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T18:30:00Z",
  "repository": {
    "name": "pmdarima",
    "remote_url": "https://github.com/alkaline-ml/pmdarima",
    "vcs": "git",
    "branch": "master",
    "tag": "v2.1.1",
    "commit": "4c2dfccb28f64d2c00a5e10b59c1d1a3e16576a9",
    "working_tree": "clean-at-source-snapshot",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "pmdarima",
      "version": "v2.1.1-source-tag; private inspection metadata reported 0.0.0",
      "import_names": ["pmdarima"]
    }
  ],
  "evidence": {
    "source_roots": ["pmdarima"],
    "docs": [
      "README.md",
      "doc/quickstart.rst",
      "doc/user_guide.rst",
      "doc/setup.rst",
      "doc/serialization.rst",
      "doc/refreshing.rst",
      "doc/tips_and_tricks.rst",
      "doc/seasonal-differencing-issues.rst",
      "doc/no-successful-model.rst",
      "doc/usecases"
    ],
    "examples": [
      "examples/example_simple_fit.py",
      "examples/example_pipeline.py",
      "examples/arima",
      "examples/model_selection",
      "examples/preprocessing",
      "examples/datasets",
      "examples/utils"
    ],
    "tests": ["pmdarima/**/tests"],
    "configs": ["pyproject.toml", "meson.build", "MANIFEST.in"]
  }
}
```

## Refresh check

- Compare `git rev-parse HEAD` with the snapshot commit.
- Compare the current exact tag and branch with `v2.1.1`/`master`.
- Recheck dynamic build metadata: the source tag and runtime distribution
  version can differ in an editable/source build.
- Refresh when public modules, estimator signatures, preprocessing return
  contracts, model-selection split geometry, persistence warnings, or the
  selected evidence paths change.

The generated runtime graph contains distilled references and safe helpers; it
does not require the source checkout to remain available.
