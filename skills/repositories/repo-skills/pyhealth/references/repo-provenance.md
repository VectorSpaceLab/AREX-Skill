# Repository Provenance

Read this before deciding whether the operating skill is current for a
PyHealth checkout. If the commit, package version, public exports, or evidence
paths differ materially, use `refresh-repo-skill`.

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T00:00:00Z",
  "repository": {
    "name": "PyHealth",
    "remote_url": "https://github.com/sunlabuiuc/PyHealth.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "0a75f99dba1fb96d6d9876790edecf252fd0d2f4",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "pyhealth",
      "version": "2.0.1",
      "import_names": ["pyhealth"]
    }
  ],
  "evidence": {
    "source_roots": ["pyhealth"],
    "docs": ["README.rst", "docs/how_to_get_started.rst", "docs/install.rst", "docs/tutorials.rst", "docs/api"],
    "examples": ["examples", "examples/tutorials"],
    "tests": ["tests", "tests/core", "tests/nlp"],
    "configs": ["pyproject.toml", "pyhealth/datasets/configs", "pyhealth/datasets/fhir/configs"]
  }
}
```

## Refresh checks

- A different commit or package version is a staleness signal.
- Public export changes in `pyhealth.datasets`, `pyhealth.tasks`,
  `pyhealth.models`, `pyhealth.processors`, `pyhealth.metrics`, or `pyhealth.medcode`
  require live API reinspection.
- If source docs remain but examples use old names, preserve the current API and
  label the example as legacy rather than treating it as a current contract.
