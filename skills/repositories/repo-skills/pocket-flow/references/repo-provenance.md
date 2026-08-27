# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a PocketFlow checkout. If the current repo commit, dirty state, package metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T07:49:21Z",
  "repository": {
    "name": "PocketFlow",
    "remote_url": "https://github.com/Tencent/PocketFlow.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "53b82cba5a34834400619e7c335a23995d45c2a6",
    "working_tree": "dirty-generated-skill-artifacts-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["learners", "nets", "datasets", "utils", "rl_agents", "automl"],
      "note": "Repository has no pyproject.toml, setup.py, or setup.cfg; it is used as a TensorFlow 1.x checkout-style source tree."
    },
    {
      "name": "tensorflow",
      "version": "1.10.0-inspection-compatible",
      "import_names": ["tensorflow"]
    }
  ],
  "evidence": {
    "source_roots": ["learners", "nets", "datasets", "utils", "rl_agents", "automl"],
    "docs": ["README.md", "docs/docs"],
    "examples": ["examples"],
    "scripts": ["scripts", "tools", "main.sh", "run.sh", "path.conf.template", "seven.yaml"],
    "tests": ["docs/docs/test_cases.md", "rl_agents/unit_tests"],
    "configs": ["path.conf.template", "automl/automl.yaml", "automl/automl_hparam.conf", "seven.yaml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and refresh it.
- If source paths outside generated `skills/` are dirty or changed, refresh it.
- If packaging metadata is added or public entry points change, refresh it.
- If PocketFlow is ported to TensorFlow 2.x or a modern packaging layout, refresh it because many setup/conversion assumptions will change.
