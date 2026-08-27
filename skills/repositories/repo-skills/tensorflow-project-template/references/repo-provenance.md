# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of TensorFlow Project Template. If the current repo commit, dirty state, package metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on the skill for new work.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T17:58:58Z",
  "repository": {
    "name": "Tensorflow-Project-Template",
    "remote_url": "https://github.com/mgsalem/Tensorflow-Project-Template.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "a7e3ce2deb83095399ce48de40f7a5ceb073fe47",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["base", "models", "trainers", "data_loader", "utils"],
      "notes": "The repository has no pyproject.toml, setup.py, or setup.cfg; it is a template checkout rather than an installable distribution."
    },
    {
      "name": "tensorflow",
      "version": "1.15.5",
      "import_names": ["tensorflow"],
      "notes": "Verified as a compatible legacy runtime for the inspected source; not declared by package metadata."
    }
  ],
  "evidence": {
    "source_roots": ["base", "models", "trainers", "data_loader", "utils", "mains"],
    "docs": ["README.md"],
    "examples": ["mains/example.py", "models/example_model.py", "trainers/example_trainer.py", "data_loader/data_generator.py"],
    "tests": [],
    "configs": ["configs/example.json"],
    "excluded": [".git", "skills", "figures/diagram.png as a runtime dependency"]
  }
}
```

The source snapshot was captured before generating this skill's own output files.

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as potentially stale.
- If source files under `base/`, `models/`, `trainers/`, `data_loader/`, `utils/`, `mains/`, `configs/`, or `README.md` changed, refresh the skill.
- If the checkout adds packaging metadata, tests, new scripts, new docs, a TensorFlow 2.x port, or a real Comet.ml integration, refresh the skill.
- If only generated review artifacts differ, that alone does not make the source evidence stale.
