# Repository Provenance

Read this before deciding whether the DeepMedic operating graph is current for
a checkout. If the commit, package version, public entry point, or evidence
paths differ, use a refresh workflow instead of assuming compatibility.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-22T03:35:00Z",
  "repository": {
    "name": "deepmedic",
    "remote_url": "https://github.com/deepmedic/deepmedic.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "e10ba7c3570d06194f5dadca91d99d5e7bba7de5",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "deepmedic",
      "version": "0.8.4",
      "import_names": ["deepmedic"]
    },
    {
      "name": "tensorflow",
      "version": "2.6.2",
      "import_names": ["tensorflow"]
    }
  ],
  "evidence": {
    "source_roots": ["deepmedic"],
    "docs": ["README.md", "documentation/README.md"],
    "examples": ["examples/configFiles"],
    "tests": [],
    "configs": ["examples/configFiles/tinyCnn", "examples/configFiles/deepMedic"],
    "scripts": ["deepMedicRun", "plotTrainingProgress.py", "setup.py"]
  }
}
```

The source checkout was dirty because this generated skill and its review
artifacts were created under `skills/`; no source implementation files were
modified for the skill.

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this graph as
  potentially stale and run `refresh-repo-skill`.
- If source implementation, setup metadata, public CLI, configuration names,
  or documented TensorFlow compatibility changes, refresh even when the commit
  is unchanged in a copied checkout.
- If a future package version changes the config parser or checkpoint format,
  re-check all four sub-skills and the bundled validators before reuse.
