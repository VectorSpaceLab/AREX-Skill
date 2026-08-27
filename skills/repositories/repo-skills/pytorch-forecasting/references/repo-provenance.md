# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package version, public API
exports, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T17:42:08Z",
  "repository": {
    "name": "pytorch-forecasting",
    "remote_url": "https://github.com/sktime/pytorch-forecasting.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "243bdbc715fdb508eaa908c9fd5d81cf5e14ce08",
    "working_tree": "clean-before-generated-skill-artifacts",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "pytorch-forecasting",
      "version": "1.8.0",
      "import_names": ["pytorch_forecasting"]
    }
  ],
  "evidence": {
    "source_roots": ["pytorch_forecasting"],
    "docs": [
      "README.md",
      "docs/source/installation.rst",
      "docs/source/getting-started.rst",
      "docs/source/data.rst",
      "docs/source/data_v2.rst",
      "docs/source/models.rst",
      "docs/source/models_v2.rst",
      "docs/source/m_layer.rst",
      "docs/source/m_layer_v2.rst",
      "docs/source/pkg.rst",
      "docs/source/pkg_v2.rst",
      "docs/source/metrics.rst",
      "docs/source/faq.rst"
    ],
    "examples": ["examples/ar.py", "examples/nbeats.py", "examples/nbeats_with_kan.py", "examples/stallion.py"],
    "tutorials": ["docs/source/tutorials"],
    "tests": ["tests", "pytorch_forecasting/tests", "pytorch_forecasting/metrics/tests"],
    "templates": ["extension_templates"],
    "configs": ["pyproject.toml", ".pre-commit-config.yaml", "CONTRIBUTING.md"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as
  potentially stale and run `refresh-repo-skill`.
- If the package metadata version, public exports, model list, v1/v2 API
  structure, optional extras, or dependency constraints changed, refresh even on
  the same commit.
- If a current checkout is dirty outside generated skill/review artifacts, check
  whether the modified source, docs, tests, or templates overlap any evidence
  path above; if yes, refresh before relying on API or workflow details.
- If API-v2 has moved from beta to stable, refresh the v2 routing and warning
  language before using production-facing v2 guidance.
