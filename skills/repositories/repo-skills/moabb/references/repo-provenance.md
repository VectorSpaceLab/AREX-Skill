# Repository Provenance

## Purpose

Read this before deciding whether the MOABB skill matches a checkout or package
installation. If the commit, dirty state, package version, public entry points,
or major evidence paths differ, use a repository-skill refresh workflow.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-22T00:00:00Z",
  "repository": {
    "name": "moabb",
    "remote_url": "https://github.com/NeuroTechX/moabb",
    "vcs": "git",
    "branch": "develop",
    "tag": null,
    "commit": "77af7c75c2fd8bbf58fbffa7cb2ae75733dc1fb8",
    "working_tree": "dirty-generated-skill-output",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "moabb",
      "version": "1.5.0.dev0",
      "import_names": ["moabb"]
    }
  ],
  "evidence": {
    "source_roots": ["moabb", "moabb/datasets", "moabb/paradigms", "moabb/pipelines", "moabb/evaluations", "moabb/analysis"],
    "docs": ["README.md", "docs/source/install", "docs/source/dataset_summary.rst", "docs/source/paper_results.rst", "docs/source/api.rst"],
    "examples": ["examples/tutorials", "examples/data_management_and_configuration", "examples/paradigm_examples", "examples/how_to_benchmark", "examples/learning_curve", "examples/advanced_examples"],
    "tests": ["moabb/tests"],
    "configs": ["pyproject.toml", "pipelines", "contexts"]
  }
}
```

## Refresh check

- If the current `git rev-parse HEAD` differs from the recorded commit, treat
  the graph as potentially stale.
- If public dataset, paradigm, pipeline, evaluation, analysis, or optional
  dependency APIs changed, refresh even when the commit is unchanged.
- The dirty `skills/` path records generated output in this checkout; it is not
  a source-package modification. Re-check source status separately before
  attributing behavior changes to the package.
