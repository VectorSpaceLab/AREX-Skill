# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of pgmpy. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill` instead of trusting stale guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T17:47:40Z",
  "repository": {
    "name": "pgmpy",
    "remote_url": "https://github.com/pgmpy/pgmpy.git",
    "vcs": "git",
    "branch": "dev",
    "tag": null,
    "commit": "fc7688eeb5061f6896c56fc0d11eed34ca3a840c",
    "working_tree": "dirty-generated-skill-output-only",
    "dirty_paths": [
      "skills/disco/pgmpy/",
      "skills/tests/pgmpy/"
    ]
  },
  "packages": [
    {
      "name": "pgmpy",
      "version": "1.1.2",
      "import_names": ["pgmpy"]
    }
  ],
  "evidence": {
    "source_roots": [
      "pgmpy/base/",
      "pgmpy/models/",
      "pgmpy/factors/",
      "pgmpy/causal_discovery/",
      "pgmpy/ci_tests/",
      "pgmpy/structure_score/",
      "pgmpy/parameter_estimator/",
      "pgmpy/inference/",
      "pgmpy/sampling/",
      "pgmpy/identification/",
      "pgmpy/prediction/",
      "pgmpy/datasets/",
      "pgmpy/example_models/",
      "pgmpy/readwrite/",
      "pgmpy/metrics/"
    ],
    "docs": [
      "README.md",
      "AGENTS.md",
      "CONTRIBUTING.md",
      "docs/guides/",
      "docs/api/"
    ],
    "examples": [
      "examples/"
    ],
    "tests": [
      "pgmpy/tests/"
    ],
    "configs": [
      "pyproject.toml",
      "devtools/extension_templates/",
      "devtools/schema/lgbn_schema.json"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, public imports, optional extras, or documented workflow guides changed, refresh even if the commit was otherwise familiar.
- If a checkout has non-generated source changes under `pgmpy/`, `docs/`, `examples/`, `devtools/`, tests, or package metadata, refresh before using maintainer-extension guidance.
- The dirty paths listed above are generated skill/review artifacts from the construction run, not source evidence changes.
